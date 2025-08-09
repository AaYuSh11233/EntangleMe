# Classiq + IonQ Setup Guide

Classiq is an end-to-end quantum software platform used to design, optimize, analyze, and execute quantum algorithms. It features a web-based IDE accessible at [https://platform.classiq.io](https://platform.classiq.io) and an accompanying Python SDK package (`pip install -U classiq`). The IDE and SDK are seamlessly integrated for a smooth workflow.

## 1. Install Required Packages

You need the Classiq SDK. Install it with:

```bash
pip install -U classiq
```

You also need the Qiskit IonQ provider if you want direct execution via Qiskit:
```bash
pip install qiskit-ionq
```

## 2. Get API Keys

- **Classiq**: Sign up at [https://platform.classiq.io](https://platform.classiq.io) and get your API key from the dashboard.
- **IonQ**: Sign up and get your API key from the API Keys section.

## 3. Set Environment Variables

On Linux/macOS:
```bash
export CLASSIQ_API_KEY="your_classiq_api_key"
export IONQ_API_KEY="your_ionq_api_key"
```

On Windows (PowerShell):
```powershell
setx CLASSIQ_API_KEY "your_classiq_api_key"
setx IONQ_API_KEY "your_ionq_api_key"
```

## 4. Create and Run a Circuit

You can create a Bell state circuit and run it on IonQ like this:

```python
from classiq import ModelBuilder, run_model
from classiq.execution import ExecutionTarget

# Create a Bell state
model = ModelBuilder().bell_state().build()

# Set IonQ QPU as execution target
execution_target = ExecutionTarget(provider="ionq", name="ionq_qpu")

# Execute
result = run_model(model=model, execution_target=execution_target)
print(result)
```
Check the `backend/app/circuits/ClassIQ.py` where a ready made example is available. For this current project. You need to just configure the ClassIQ and Ionq and use the ready made code also.

## 5. Notes

- You **do not** need to explicitly create a `Client()` instance unless you want advanced control.
- The SDK uses your `CLASSIQ_API_KEY` automatically from the environment variables.
- IonQ execution will use your `IONQ_API_KEY`.

