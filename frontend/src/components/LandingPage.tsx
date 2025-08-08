import { motion } from "framer-motion";
import { IconBrandGithub } from "@tabler/icons-react";
import { AnimatedBackground } from "./ui/custom/animated-background";
import { Button } from "./ui/button";
import { AspectRatio } from "./ui/custom/aspect-ratio";
import { useState } from "react";
import { UserNameDialog } from "./chat/UserNameDialog";

interface LandingPageProps {
  onGetStarted: (username: string) => void;
}

const features = [
  {
    title: "Quantum-Powered",
    description: "Utilizing real quantum teleportation principles for message transfer",
  },
  {
    title: "Secure by Nature",
    description: "Inherent security through quantum mechanics principles",
  },
  {
    title: "Real-time Chat",
    description: "Instant quantum state transmission and visualization",
  },
];

const whyItMatters = [
  {
    title: "Quantum-Resistant Messaging",
    description: "By transforming our simulated teleportation pipeline into a true QKD channel, Entangleme can use the randomly generated measurement outcomes as shared secret keys. After each teleportation, those key bits encrypt classical payloads—guaranteeing that any eavesdropping attempt is immediately detectable.",
  },
  {
    title: "Hybrid Quantum-Classical Workflows",
    description: "Not all users have direct access to quantum hardware. Entangleme's modular Flask API and frontend architecture can be deployed as serverless functions or at the network edge, running lightweight quantum simulations close to the user.",
  },
  {
    title: "On-Ramp to the Quantum Internet",
    description: "As quantum repeaters and entanglement distribution networks become available, Entangleme's 'simulator-swap' design lets us replace Qiskit's backend with live hardware with minimal code changes.",
  },
];

const team = [
  {
    name: "Md Athar Jamal Makki",
    role: "🧠 Lead",
    github: "https://github.com/atharhive",
  },
  {
    name: "Akshad Jogi",
    role: "🎨 Frontend",
    github: "https://github.com/akshad-exe",
  },
  {
    name: "Ayush Sarkar",
    role: "🛠 Backend",
    github: "https://github.com/dev-Ninjaa",
  },
];

export function LandingPage({ onGetStarted }: LandingPageProps) {
  const [showDialog, setShowDialog] = useState(false);

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-transparent">
      <AnimatedBackground />
      
      <div className="relative z-10">
        <div className="container mx-auto px-4">
          <header className="py-6">
            <nav className="flex justify-between items-center">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5 }}
                className="text-2xl font-bold text-white flex items-center gap-2"
              >
                <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center backdrop-blur-sm">
                  🌀
                </div>
                EntangleMe
              </motion.div>
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5 }}
              >
                <a
                  href="https://github.com/dev-Ninjaa/EntangleMe"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-blue-400 transition-colors text-white"
                >
                  <IconBrandGithub size={24} />
                </a>
              </motion.div>
            </nav>
          </header>

          <main className="py-20">
            <div className="max-w-4xl mx-auto text-center mb-32">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="relative"
              >
                <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-500 to-blue-600 pb-2">
                  Quantum Chat for the Future
                </h1>
                <div className="absolute -inset-x-20 top-0 h-[400px] w-[800px] bg-gradient-to-r from-blue-500 to-purple-500 opacity-20 blur-2xl" />
              </motion.div>
              
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.2 }}
                className="text-xl md:text-2xl text-gray-300 mb-12"
              >
                Experience a simulation of future quantum networks through secure messaging
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
                className="flex gap-4 justify-center"
              >
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-blue-500 via-purple-500 to-blue-600 hover:opacity-90 transition-opacity text-white px-8"
                  onClick={() => setShowDialog(true)}
                >
                  Get Started
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="border-blue-500 text-blue-400 hover:bg-blue-500/10"
                >
                  Learn More
                </Button>
              </motion.div>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1, delay: 0.6 }}
              className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 text-center"
            >
              {features.map((feature, index) => (
                <motion.div
                  key={index}
                  whileHover={{ scale: 1.05 }}
                  className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10 hover:border-blue-500/50 transition-colors"
                >
                  <h3 className="text-xl font-semibold mb-3 text-white">{feature.title}</h3>
                  <p className="text-gray-400">{feature.description}</p>
                </motion.div>
              ))}
            </motion.div>

            <motion.section
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.8 }}
              className="mt-32"
            >
              <div className="max-w-4xl mx-auto">
                <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
                  Why EntangleMe Matters?
                </h2>
                <div className="space-y-12">
                  {whyItMatters.map((item, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.6 }}
                      className="bg-white/5 rounded-lg p-6 backdrop-blur-sm border border-white/10"
                    >
                      <h3 className="text-xl font-semibold mb-4 text-blue-400">{item.title}</h3>
                      <p className="text-gray-300 leading-relaxed">{item.description}</p>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.section>

            <motion.section
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.8 }}
              className="mt-32 text-center"
            >
              <h2 className="text-3xl md:text-4xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
                Core Concept
              </h2>
              <div className="max-w-3xl mx-auto bg-white/5 rounded-lg p-8 backdrop-blur-sm border border-white/10">
                <p className="text-xl text-gray-300 italic">
                  "Entangle → Encode → Measure → Send Classical Bits → Apply Corrections"
                </p>
                <p className="mt-4 text-gray-400">
                  This is the same foundation used in quantum internet and secure quantum communication.
                </p>
              </div>
            </motion.section>

            <motion.section
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.8 }}
              className="mt-32 text-center"
            >
              <h2 className="text-3xl md:text-4xl font-bold mb-12 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
                Meet the Team
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {team.map((member, index) => (
                  <motion.a
                    key={index}
                    href={member.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    whileHover={{ scale: 1.05 }}
                    className="bg-white/5 rounded-lg p-6 backdrop-blur-sm border border-white/10 hover:border-blue-500/50 transition-colors"
                  >
                    <h3 className="text-xl font-semibold text-white mb-2">{member.name}</h3>
                    <p className="text-blue-400 mb-2">{member.role}</p>
                    <p className="text-gray-400">@{member.github.split('/').pop()}</p>
                  </motion.a>
                ))}
              </div>
            </motion.section>
          </main>
        </div>
      </div>

      <UserNameDialog
        isOpen={showDialog}
        onClose={() => setShowDialog(false)}
        onGetStarted={onGetStarted}
      />
    </div>
  );
} 