import { motion } from 'framer-motion';
import { TrendingUp, Target, CheckCircle, BarChart3, PieChart } from 'lucide-react';

const Results = () => {
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

  const metrics = [
    {
      name: "Accuracy",
      value: "95.8%",
      icon: <Target className="w-6 h-6" />,
      color: "from-green-500 to-green-600",
      description: "Overall classification accuracy"
    },
    {
      name: "Precision",
      value: "94.2%",
      icon: <CheckCircle className="w-6 h-6" />,
      color: "from-blue-500 to-blue-600",
      description: "True positive rate"
    },
    {
      name: "Recall",
      value: "93.7%",
      icon: <TrendingUp className="w-6 h-6" />,
      color: "from-purple-500 to-purple-600",
      description: "Sensitivity to anomalies"
    },
    {
      name: "F1-Score",
      value: "93.9%",
      icon: <BarChart3 className="w-6 h-6" />,
      color: "from-orange-500 to-orange-600",
      description: "Harmonic mean of precision and recall"
    },
    {
      name: "ROC-AUC",
      value: "0.976",
      icon: <PieChart className="w-6 h-6" />,
      color: "from-pink-500 to-pink-600",
      description: "Area under ROC curve"
    }
  ];

  const modelComparison = [
    {
      model: "Random Forest",
      accuracy: "94.2%",
      f1Score: "93.1%",
      trainingTime: "2.3s",
      predictionTime: "0.1ms"
    },
    {
      model: "XGBoost",
      accuracy: "95.8%",
      f1Score: "93.9%",
      trainingTime: "5.7s",
      predictionTime: "0.2ms"
    },
    {
      model: "LSTM",
      accuracy: "92.1%",
      f1Score: "91.4%",
      trainingTime: "45.2s",
      predictionTime: "1.2ms"
    },
    {
      model: "Autoencoder",
      accuracy: "89.7%",
      f1Score: "88.9%",
      trainingTime: "38.9s",
      predictionTime: "0.8ms"
    }
  ];

  return (
    <section id="results" className="py-20 bg-white">
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
            Model Performance Results
          </motion.h2>
          <motion.p
            variants={itemVariants}
            className="text-xl text-gray-600 max-w-3xl mx-auto"
          >
            Comprehensive evaluation metrics
          </motion.p>
        </motion.div>

        {/* Metrics */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-16"
        >
          {metrics.map((metric, index) => (
            <motion.div
              key={index}
              variants={itemVariants}
              className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2"
            >
              <div className={`w-12 h-12 bg-gradient-to-r ${metric.color} rounded-lg flex items-center justify-center text-white mb-4`}>
                {metric.icon}
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{metric.name}</h3>
              <div className="text-3xl font-bold text-gray-900 mb-2">{metric.value}</div>
              <p className="text-sm text-gray-600">{metric.description}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Model Comparison */}
        {/* <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          <motion.div variants={itemVariants} className="text-center mb-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-4">Model Comparison</h3>
            <p className="text-gray-600">Performance metrics across different ML/DL approaches</p>
          </motion.div>

          <motion.div variants={itemVariants} className="bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Model</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Accuracy</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">F1-Score</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Training Time</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Prediction Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {modelComparison.map((model, index) => (
                    <tr key={index} className="hover:bg-gray-50 transition-colors duration-200">
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{model.model}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{model.accuracy}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{model.f1Score}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{model.trainingTime}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{model.predictionTime}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </motion.div> */}

      </div>
    </section>
  );
};

export default Results;