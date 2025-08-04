import ast
import functools
import warnings
from abc import abstractmethod
from dataclasses import is_dataclass
from enum import EnumMeta
from inspect import isclass
from typing import Any, Callable, Optional, get_origin

from classiq.interface.exceptions import ClassiqDeprecationWarning, ClassiqError
from classiq.interface.executor.execution_preferences import ExecutionPreferences
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.generator.model.constraints import Constraints
from classiq.interface.generator.model.preferences.preferences import Preferences
from classiq.interface.generator.types.compilation_metadata import CompilationMetadata
from classiq.interface.model.model import MAIN_FUNCTION_NAME, Model
from classiq.interface.model.native_function_definition import (
    NativeFunctionDefinition,
)
from classiq.interface.model.quantum_function_declaration import (
    NamedParamsQuantumFunctionDeclaration,
)

from classiq.qmod.classical_function import CFunc
from classiq.qmod.cparam import CParamAbstract
from classiq.qmod.declaration_inferrer import infer_func_decl, is_qvar
from classiq.qmod.generative import set_frontend_interpreter
from classiq.qmod.global_declarative_switch import get_global_declarative_switch
from classiq.qmod.qmod_constant import QConstant
from classiq.qmod.qmod_parameter import CArray, CParamList
from classiq.qmod.quantum_callable import QCallable, QCallableList
from classiq.qmod.quantum_expandable import QExpandable, QTerminalCallable
from classiq.qmod.semantics.annotation.qstruct_annotator import QStructAnnotator
from classiq.qmod.semantics.validation.main_validation import validate_main_function
from classiq.qmod.utilities import mangle_keyword


class BaseQFunc(QExpandable):
    def __init__(
        self,
        py_callable: Callable,
        compilation_metadata: Optional[CompilationMetadata] = None,
    ) -> None:
        super().__init__(py_callable)
        functools.update_wrapper(self, py_callable)
        self.compilation_metadata = compilation_metadata

    @property
    def func_decl(self) -> NamedParamsQuantumFunctionDeclaration:
        raise NotImplementedError

    @property
    def pure_decl(self) -> NamedParamsQuantumFunctionDeclaration:
        if type(self.func_decl) is NamedParamsQuantumFunctionDeclaration:
            return self.func_decl
        return NamedParamsQuantumFunctionDeclaration(
            **{
                k: v
                for k, v in self.func_decl.model_dump().items()
                if k in NamedParamsQuantumFunctionDeclaration.model_fields
            }
        )

    @property
    def _has_inputs(self) -> bool:
        return any(
            port.direction == PortDeclarationDirection.Input
            for port in self.func_decl.port_declarations
        )

    def update_compilation_metadata(self, **kwargs: Any) -> None:
        if kwargs.get("should_synthesize_separately") and self._has_inputs:
            raise ClassiqError("Can't synthesize separately a function with inputs")
        self.compilation_metadata = self._compilation_metadata.model_copy(update=kwargs)

    @property
    def _compilation_metadata(self) -> CompilationMetadata:
        if self.compilation_metadata is None:
            return CompilationMetadata()
        return self.compilation_metadata

    @abstractmethod
    def create_model(
        self,
        constraints: Optional[Constraints] = None,
        execution_preferences: Optional[ExecutionPreferences] = None,
        preferences: Optional[Preferences] = None,
        classical_execution_function: Optional[CFunc] = None,
    ) -> Model:
        pass


class QFunc(BaseQFunc):
    FRAME_DEPTH = 3

    def __init__(
        self,
        py_callable: Callable,
        compilation_metadata: Optional[CompilationMetadata] = None,
    ) -> None:
        _validate_no_gen_params(py_callable.__annotations__)
        super().__init__(py_callable, compilation_metadata)
        if compilation_metadata is not None and compilation_metadata.unchecked:
            self.compilation_metadata: Optional[CompilationMetadata] = (
                CompilationMetadata(unchecked=compilation_metadata.unchecked)
            )
        else:
            self.compilation_metadata = None

    @property
    def func_decl(self) -> NamedParamsQuantumFunctionDeclaration:
        name = self._py_callable.__name__
        if name in self._qmodule.native_defs:
            return self._qmodule.native_defs[name]
        return infer_func_decl(self._py_callable, qmodule=self._qmodule)

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        self.expand()
        super().__call__(*args, **kwargs)

    def create_model(
        self,
        constraints: Optional[Constraints] = None,
        execution_preferences: Optional[ExecutionPreferences] = None,
        preferences: Optional[Preferences] = None,
        classical_execution_function: Optional[CFunc] = None,
    ) -> Model:
        self._qmodule.reset()
        QConstant.set_current_model(self._qmodule)
        self.expand()
        model_extra_settings: list[tuple[str, Any]] = [
            ("constraints", constraints),
            ("execution_preferences", execution_preferences),
            ("preferences", preferences),
        ]
        if classical_execution_function is not None:
            self._add_constants_from_classical_code(classical_execution_function)
            model_extra_settings.append(
                ("classical_execution_code", classical_execution_function.code)
            )
        model = Model(
            constants=list(self._qmodule.constants.values()),
            functions=list(self._qmodule.native_defs.values()),
            enums=list(self._qmodule.enum_decls.values()),
            types=list(self._qmodule.type_decls.values()),
            qstructs=list(self._qmodule.qstruct_decls.values()),
            functions_compilation_metadata=self._qmodule.functions_compilation_metadata,
            **{key: value for key, value in model_extra_settings if value},
        )
        if (
            not get_global_declarative_switch()
            and len(self._qmodule.generative_functions) > 0
        ):
            return self._create_generative_model(model)
        return model

    def _create_generative_model(self, model_stub: Model) -> Model:
        from classiq.model_expansions.interpreters.frontend_generative_interpreter import (
            FrontendGenerativeInterpreter,
        )
        from classiq.qmod.semantics.annotation.call_annotation import (
            resolve_function_calls,
        )

        generative_functions = list(self._qmodule.generative_functions.values())
        QStructAnnotator().visit(model_stub)
        for gen_func in generative_functions:
            QStructAnnotator().visit(gen_func.func_decl)
        resolve_function_calls(
            model_stub,
            dict(model_stub.function_dict)
            | {
                gen_func.func_decl.name: gen_func.func_decl
                for gen_func in generative_functions
            },
        )
        interpreter = FrontendGenerativeInterpreter(model_stub, generative_functions)
        set_frontend_interpreter(interpreter)
        return interpreter.expand()

    def expand(self) -> None:
        if self.func_decl.name in self._qmodule.native_defs:
            return
        super().expand()
        self._qmodule.native_defs[self.func_decl.name] = NativeFunctionDefinition(
            **{**self.func_decl.model_dump(), **{"body": self.body}}
        )
        if self.compilation_metadata is not None:
            self._qmodule.functions_compilation_metadata[self.func_decl.name] = (
                self.compilation_metadata
            )

    def _add_constants_from_classical_code(
        self, classical_execution_function: CFunc
    ) -> None:
        # FIXME: https://classiq.atlassian.net/browse/CAD-18050
        # We use this visitor to add the constants that were used in the classical
        # execution code to the model. In the future, if we will have a better notion
        # of "QModule" and a "QConstant" will be a part of it then we may be able to
        # remove the handling of the QConstants from this visitor, but I think we will
        # need similar logic to allow using python variables in the classical execution
        # code
        class IdentifierVisitor(ast.NodeVisitor):
            def visit_Name(self, node: ast.Name) -> None:
                if (
                    node.id in classical_execution_function._caller_constants
                    and isinstance(
                        classical_execution_function._caller_constants[node.id],
                        QConstant,
                    )
                ):
                    classical_execution_function._caller_constants[
                        node.id
                    ].add_to_model()

        IdentifierVisitor().visit(ast.parse(classical_execution_function.code))


class ExternalQFunc(QTerminalCallable):
    FRAME_DEPTH = 2  # FIXME: Remove (CLS-2912)
    _decl: NamedParamsQuantumFunctionDeclaration

    def __init__(self, py_callable: Callable) -> None:
        self._py_callable = py_callable
        decl = infer_func_decl(py_callable)

        py_callable.__annotations__.pop("return", None)
        if py_callable.__annotations__.keys() != {
            mangle_keyword(arg.name) for arg in decl.positional_arg_declarations
        }:
            raise ClassiqError(
                f"Parameter type hints for {py_callable.__name__!r} do not match imported declaration"
            )
        super().__init__(decl)
        functools.update_wrapper(self, py_callable)

    @property
    def func_decl(self) -> NamedParamsQuantumFunctionDeclaration:
        return self._decl

    @property
    def pure_decl(self) -> NamedParamsQuantumFunctionDeclaration:
        return self.func_decl

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        if self._py_callable.__name__ == "parametric_suzuki_trotter":
            warnings.warn(
                (
                    "Function 'parametric_suzuki_trotter' is deprecated and will no "
                    "longer be supported starting on 21/7/2025 at the earliest. "
                    "Instead, use 'multi_suzuki_trotter'."
                ),
                ClassiqDeprecationWarning,
                stacklevel=2,
            )
        if self._py_callable.__name__ == "sparse_suzuki_trotter":
            warnings.warn(
                (
                    "Function 'sparse_suzuki_trotter' is deprecated and will no "
                    "longer be supported starting on 21/7/2025 at the earliest. "
                    "Instead, use 'suzuki_trotter'."
                ),
                ClassiqDeprecationWarning,
                stacklevel=2,
            )
        if (
            self._py_callable.__name__ == "suzuki_trotter"
            and len(args) > 0
            and isinstance(args[0], (list, CParamList))
        ):
            warnings.warn(
                (
                    "Parameter type CArray[PauliTerm] to function 'suzuki_trotter' is "
                    "deprecated and will no longer be supported starting on 21/7/2025 "
                    "at the earliest. Instead, send a 'SparsePauliOp' (see "
                    "https://docs.classiq.io/latest/qmod-reference/language-reference/classical-types/#hamiltonians)."
                ),
                ClassiqDeprecationWarning,
                stacklevel=2,
            )
        super().__call__(*args, **kwargs)


class GenerativeQFunc(BaseQFunc):
    FRAME_DEPTH = 3

    def __init__(
        self,
        py_callable: Callable,
        func_decl: Optional[NamedParamsQuantumFunctionDeclaration] = None,
        compilation_metadata: Optional[CompilationMetadata] = None,
    ) -> None:
        super().__init__(py_callable, compilation_metadata)
        self._func_decl = func_decl
        self._inferred_func_decl: Optional[NamedParamsQuantumFunctionDeclaration] = None

    @property
    def func_decl(self) -> NamedParamsQuantumFunctionDeclaration:
        if self._func_decl is not None:
            return self._func_decl
        if self._inferred_func_decl is None:
            self._inferred_func_decl = infer_func_decl(self._py_callable, self._qmodule)
        return self._inferred_func_decl

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        if get_global_declarative_switch():
            return QFunc(self._py_callable, self.compilation_metadata)(*args, **kwargs)
        if self.func_decl.name not in self._qmodule.generative_functions:
            self._qmodule.generative_functions[self.func_decl.name] = self
            if self._func_decl is None:
                self._inferred_func_decl = infer_func_decl(
                    self._py_callable, self._qmodule
                )
        super().__call__(*args, **kwargs)

    def create_model(
        self,
        constraints: Optional[Constraints] = None,
        execution_preferences: Optional[ExecutionPreferences] = None,
        preferences: Optional[Preferences] = None,
        classical_execution_function: Optional[CFunc] = None,
    ) -> Model:
        if get_global_declarative_switch():
            return QFunc(self._py_callable).create_model(
                constraints,
                execution_preferences,
                preferences,
                classical_execution_function,
            )
        self._qmodule.reset()
        if self.func_decl.name == MAIN_FUNCTION_NAME:
            validate_main_function(self.func_decl)

        def _dec_main(*args: Any, **kwargs: Any) -> None:
            self(*args, **kwargs)

        _dec_main.__annotations__ = self._py_callable.__annotations__

        return QFunc(_dec_main).create_model(
            constraints=constraints,
            execution_preferences=execution_preferences,
            preferences=preferences,
            classical_execution_function=classical_execution_function,
        )


ILLEGAL_PARAM_ERROR = "Unsupported type hint '{annotation}' for argument '{name}'."


class IllegalParamsError(ClassiqError):
    _HINT = (
        "\nNote - QMOD functions can declare classical parameters using the type hints "
        "'CInt', 'CReal', 'CBool', and 'CArray'."
    )

    def __init__(self, message: str) -> None:
        super().__init__(message + self._HINT)


def _validate_no_gen_params(annotations: dict[str, Any]) -> None:
    _illegal_params = {
        name: annotation
        for name, annotation in annotations.items()
        if not (
            name == "return"
            or (isclass(annotation) and issubclass(annotation, CParamAbstract))
            or (isclass(annotation) and is_dataclass(annotation))
            or (isclass(annotation) and isinstance(annotation, EnumMeta))
            or get_origin(annotation) is CArray
            or (get_origin(annotation) or annotation) is QCallable
            or (get_origin(annotation) or annotation) is QCallableList
            or is_qvar(annotation)
        )
    }
    if _illegal_params:
        raise IllegalParamsError(
            "\n".join(
                ILLEGAL_PARAM_ERROR.format(name=name, annotation=annotation)
                for name, annotation in _illegal_params.items()
            )
        )
