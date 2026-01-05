import { motion } from 'framer-motion';
import { Database, Brain, Cpu, Target, TrendingUp, Shield } from 'lucide-react';

const ProjectOverview = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        delayChildren: 0.2,
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 30, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1
    }
  };

  const purposeFeatures = [
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Network Security",
      description: "Detect and prevent cyber threats in real-time network traffic"
    },
    {
      icon: <Brain className="w-6 h-6" />,
      title: "AI-Powered Detection",
      description: "Leverage machine learning for intelligent anomaly identification"
    },
    {
      icon: <Target className="w-6 h-6" />,
      title: "High Accuracy",
      description: "Achieve superior detection rates with minimal false positives"
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "Scalable Solution",
      description: "Handle large-scale network monitoring efficiently"
    }
  ];

  const datasets = [
    {
      name: "CICIDS2017",
      description: "Comprehensive dataset with benign and common attack scenarios",
      features: "2.8M flows, 78 features, 7 attack categories"
    },
    {
      name: "NSL-KDD",
      description: "Refined version of KDD Cup 99 with reduced redundancy",
      features: "148K samples, 41 features, 4 attack types"
    }
  ];

  const models = [
    {
      name: "Random Forest",
      type: "Ensemble ML",
      description: "Robust tree-based classifier with excellent generalization"
    },
    {
      name: "XGBoost",
      type: "Gradient Boosting",
      description: "High-performance gradient boosting for complex patterns"
    },
    {
      name: "LSTM",
      type: "Deep Learning",
      description: "Long Short-Term Memory networks for sequential patterns"
    },
    {
      name: "Autoencoder",
      type: "Deep Learning",
      description: "Unsupervised anomaly detection using reconstruction error"
    }
  ];

  return (
    <section id="methodology" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
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
            Project Overview
          </motion.h2>
          <motion.p
            variants={itemVariants}
            className="text-xl text-gray-600 max-w-3xl mx-auto"
          >
            A comprehensive machine learning solution for detecting network anomalies and cyber threats
          </motion.p>
        </motion.div>

        {/* Purpose Section */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mb-20"
        >
          <motion.div variants={itemVariants} className="text-center mb-12">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">Project Purpose</h3>
            <p className="text-lg text-gray-700 max-w-4xl mx-auto leading-relaxed">
              Network anomaly detection is crucial for maintaining cybersecurity in today's digital landscape. 
              As cyber threats become more sophisticated, traditional rule-based security systems struggle to 
              keep pace. Our solution leverages advanced machine learning and deep learning algorithms to 
              automatically identify unusual network patterns that may indicate malicious activities such as 
              DDoS attacks, intrusion attempts, or data exfiltration.
            </p>
          </motion.div>

          <motion.div
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8"
          >
            {purposeFeatures.map((feature, index) => (
              <motion.div
                key={index}
                variants={itemVariants}
                className="bg-gradient-to-br from-blue-50 to-purple-50 p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2"
              >
                <div className="text-primary-600 mb-4">{feature.icon}</div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h4>
                <p className="text-gray-600">{feature.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>

        {/* Datasets Section */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mb-20"
        >
          <motion.div variants={itemVariants} className="text-center mb-12">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">Datasets Used</h3>
            <p className="text-lg text-gray-700 max-w-3xl mx-auto">
              Our models are trained and evaluated on industry-standard network security datasets
            </p>
          </motion.div>

          <motion.div
            variants={containerVariants}
            className="grid grid-cols-1 lg:grid-cols-2 gap-8"
          >
            {datasets.map((dataset, index) => (
              <motion.div
                key={index}
                variants={itemVariants}
                className="bg-white border border-gray-200 rounded-xl p-8 shadow-lg hover:shadow-xl transition-all duration-300"
              >
                <div className="flex items-center mb-4">
                  <Database className="w-8 h-8 text-primary-600 mr-3" />
                  <h4 className="text-xl font-bold text-gray-900">{dataset.name}</h4>
                </div>
                <p className="text-gray-700 mb-4">{dataset.description}</p>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 font-medium">{dataset.features}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>

        {/* Models Section */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          <motion.div variants={itemVariants} className="text-center mb-12">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">ML/DL Models</h3>
            <p className="text-lg text-gray-700 max-w-3xl mx-auto">
              Comprehensive comparison of traditional and modern approaches to anomaly detection
            </p>
          </motion.div>

          <motion.div
            variants={containerVariants}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {models.map((model, index) => (
              <motion.div
                key={index}
                variants={itemVariants}
                className="bg-gradient-to-br from-gray-50 to-blue-50 border border-gray-200 rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
              >
                <div className="flex items-center mb-3">
                  <Cpu className="w-6 h-6 text-primary-600 mr-2" />
                  <span className="text-sm font-medium text-primary-600 bg-primary-100 px-2 py-1 rounded">
                    {model.type}
                  </span>
                </div>
                <h4 className="text-lg font-bold text-gray-900 mb-2">{model.name}</h4>
                <p className="text-gray-600 text-sm">{model.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};

export default ProjectOverview;
