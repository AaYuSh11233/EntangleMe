import { useNavigate } from "react-router-dom";
import Lottie from "lottie-react";
import { Button } from "./ui/button";
import notFoundAnimation from "../assets/animations/404.json";  


export function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-2xl mx-auto text-center">
        <div className="w-full max-w-[500px] mx-auto mb-8">
          <Lottie
            animationData={notFoundAnimation}
            loop={true}
            autoplay={true}
            rendererSettings={{
              preserveAspectRatio: "xMidYMid slice"
            }}
            className="w-full h-full"
          />
        </div>
        <h1 className="text-4xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
          Page Not Found
        </h1>
        <p className="text-muted-foreground mb-8">
          Oops! It seems like this quantum state doesn't exist.
        </p>
        <Button
          onClick={() => navigate("/")}
          className="bg-gradient-to-r from-blue-500 via-purple-500 to-blue-600 hover:opacity-90 transition-opacity text-white px-8"
        >
          Return Home
        </Button>
      </div>
    </div>
  );
} 