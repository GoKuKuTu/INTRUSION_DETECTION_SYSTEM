import { motion } from "framer-motion";
import {
  Server,
  Brain,
  Cpu,
  Database,
  Globe,
  Code,
  Layers,
  Box,     // ✅ used instead of 'Container'
} from "lucide-react";

const TechStack = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        delayChildren: 0.2,
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 30, opacity: 0 },
    visible: { y: 0, opacity: 1 },
  };

  const technologies = [
    {
      category: "Backend & API",
      icon: <Server className="w-8 h-8" />,
      color: "from-blue-500 to-blue-600",
      items: [
        { name: "Python", description: "Core programming language" },
        { name: "FastAPI", description: "High-performance web framework" },
        { name: "Uvicorn", description: "ASGI server for API hosting" },
      ],
    },
    {
      category: "Machine Learning",
      icon: <Brain className="w-8 h-8" />,
      color: "from-purple-500 to-purple-600",
      items: [
        { name: "Scikit-Learn", description: "Traditional ML algorithms" },
        { name: "XGBoost", description: "Gradient boosting framework" },
        { name: "Pandas", description: "Data manipulation and analysis" },
      ],
    },
    {
      category: "Deep Learning",
      icon: <Layers className="w-8 h-8" />,
      color: "from-green-500 to-green-600",
      items: [
        { name: "TensorFlow", description: "Deep learning framework" },
        { name: "Keras", description: "High-level neural networks API" },
        { name: "NumPy", description: "Numerical computing library" },
      ],
    },
    {
      category: "Data & Processing",
      icon: <Database className="w-8 h-8" />,
      color: "from-orange-500 to-orange-600",
      items: [
        { name: "Pandas", description: "Data manipulation and analysis" },
        { name: "NumPy", description: "Numerical computing" },
        { name: "Matplotlib", description: "Data visualization" },
      ],
    },
    {
      category: "Containerization",
      icon: <Box className="w-8 h-8" />, // ✅ Replaced 'Container' with 'Box'
      color: "from-indigo-500 to-indigo-600",
      items: [
        { name: "Docker", description: "Containerization platform" },
        { name: "Docker Compose", description: "Multi-container orchestration" },
      ],
    },
    {
      category: "Frontend",
      icon: <Globe className="w-8 h-8" />,
      color: "from-pink-500 to-pink-600",
      items: [
        { name: "React", description: "Modern UI library" },
        { name: "Tailwind CSS", description: "Utility-first CSS framework" },
        { name: "Vite", description: "Fast build tool" },
      ],
    },
  ];

  const additionalTools = [
    { name: "Jupyter Notebooks", purpose: "Interactive development and analysis" },
    { name: "Git", purpose: "Version control and collaboration" },
    { name: "GitHub Actions", purpose: "CI/CD automation" },
    { name: "pytest", purpose: "Testing framework" },
    { name: "Black", purpose: "Code formatting" },
    { name: "Flake8", purpose: "Code linting" },
  ];

  return (
    <section className="py-20 bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <motion.h2
            variants={itemVariants}
            className="text-3xl md:text-4xl font-bold text-gray-900 mb-6"
          >
            Technology Stack
          </motion.h2>
          <motion.p
            variants={itemVariants}
            className="text-xl text-gray-600 max-w-3xl mx-auto"
          >
            Built with modern technologies and best practices for scalable, maintainable code.
          </motion.p>
        </motion.div>

        {/* Technology Categories */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16"
        >
          {technologies.map((tech, index) => (
            <motion.div
              key={index}
              variants={itemVariants}
              className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2"
            >
              <div className={`bg-gradient-to-r ${tech.color} p-6 rounded-t-xl`}>
                <div className="flex items-center text-white">
                  {tech.icon}
                  <h3 className="text-xl font-bold ml-3">{tech.category}</h3>
                </div>
              </div>

              <div className="p-6 space-y-4">
                {tech.items.map((item, itemIndex) => (
                  <div key={itemIndex} className="border-l-4 border-primary-200 pl-4">
                    <h4 className="font-semibold text-gray-900">{item.name}</h4>
                    <p className="text-sm text-gray-600">{item.description}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Additional Tools */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          <motion.div variants={itemVariants} className="text-center mb-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              Additional Tools & Libraries
            </h3>
            <p className="text-gray-600">
              Supporting tools for development, testing, and deployment.
            </p>
          </motion.div>

          <motion.div
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {additionalTools.map((tool, index) => (
              <motion.div
                key={index}
                variants={itemVariants}
                className="bg-white rounded-lg p-4 shadow-md hover:shadow-lg transition-all duration-300 border-l-4 border-primary-500"
              >
                <h4 className="font-semibold text-gray-900 mb-1">{tool.name}</h4>
                <p className="text-sm text-gray-600">{tool.purpose}</p>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>

        {/* Architecture Overview */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mt-16"
        >
          <motion.div variants={itemVariants} className="text-center mb-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">
              System Architecture
            </h3>
            <p className="text-gray-600">
              End-to-end pipeline from data processing to deployment.
            </p>
          </motion.div>

          <motion.div variants={itemVariants} className="bg-white rounded-xl shadow-lg p-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Database className="w-8 h-8 text-blue-600" />
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Data Layer</h4>
                <p className="text-sm text-gray-600">CICIDS2017, NSL-KDD datasets</p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Cpu className="w-8 h-8 text-purple-600" />
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Processing</h4>
                <p className="text-sm text-gray-600">Preprocessing & Feature Engineering</p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Brain className="w-8 h-8 text-green-600" />
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Models</h4>
                <p className="text-sm text-gray-600">ML/DL Training & Validation</p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Server className="w-8 h-8 text-orange-600" />
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Deployment</h4>
                <p className="text-sm text-gray-600">FastAPI + Docker</p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};

export default TechStack;
