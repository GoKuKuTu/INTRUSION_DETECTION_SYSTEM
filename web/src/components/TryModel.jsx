import { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

const TryModel = () => {
  const [formData, setFormData] = useState({
    feature1: '',
    feature2: '',
    feature3: '',
    feature4: '',
    feature5: ''
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Convert form data to numeric array
      const features = [
        parseFloat(formData.feature1) || 0,
        parseFloat(formData.feature2) || 0,
        parseFloat(formData.feature3) || 0,
        parseFloat(formData.feature4) || 0,
        parseFloat(formData.feature5) || 0
      ];

      // API endpoint (configurable). Set VITE_API_URL in web/.env when running locally
      const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const params = new URLSearchParams({ model: 'ml', path: 'models/full_model.pkl' })
      const response = await fetch(`${API_BASE}/predict?${params.toString()}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          features: features
        })
      });
      let data;
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        data = { detail: text };
      }
      if (!response.ok) {
        const detail = (data && (data.detail || data.message)) || `HTTP ${response.status}`;
        throw new Error(String(detail));
      }
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <section className="py-20 bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <motion.h2
            variants={itemVariants}
            className="text-3xl md:text-4xl font-bold text-gray-900 mb-6"
          >
            Try the Model
          </motion.h2>
          <motion.p
            variants={itemVariants}
            className="text-xl text-gray-600 max-w-3xl mx-auto"
          >
            Test our anomaly detection model with your own input features
          </motion.p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-8"
        >
          {/* Input Form */}
          <motion.div variants={itemVariants}>
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">Input Features</h3>
              
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label htmlFor="feature1" className="block text-sm font-medium text-gray-700 mb-2">
                    Feature 1 (Flow Duration)
                  </label>
                  <input
                    type="number"
                    id="feature1"
                    name="feature1"
                    step="0.1"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors duration-200"
                    placeholder="e.g., 100.5"
                    value={formData.feature1}
                    onChange={handleInputChange}
                    required
                  />
                </div>

                <div>
                  <label htmlFor="feature2" className="block text-sm font-medium text-gray-700 mb-2">
                    Feature 2 (Packet Count)
                  </label>
                  <input
                    type="number"
                    id="feature2"
                    name="feature2"
                    step="0.1"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors duration-200"
                    placeholder="e.g., 50.0"
                    value={formData.feature2}
                    onChange={handleInputChange}
                    required
                  />
                </div>

                <div>
                  <label htmlFor="feature3" className="block text-sm font-medium text-gray-700 mb-2">
                    Feature 3 (Byte Count)
                  </label>
                  <input
                    type="number"
                    id="feature3"
                    name="feature3"
                    step="0.1"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors duration-200"
                    placeholder="e.g., 1024.0"
                    value={formData.feature3}
                    onChange={handleInputChange}
                    required
                  />
                </div>

                <div>
                  <label htmlFor="feature4" className="block text-sm font-medium text-gray-700 mb-2">
                    Feature 4 (Protocol Type)
                  </label>
                  <input
                    type="number"
                    id="feature4"
                    name="feature4"
                    step="0.1"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors duration-200"
                    placeholder="e.g., 1.0"
                    value={formData.feature4}
                    onChange={handleInputChange}
                    required
                  />
                </div>

                <div>
                  <label htmlFor="feature5" className="block text-sm font-medium text-gray-700 mb-2">
                    Feature 5 (Port Number)
                  </label>
                  <input
                    type="number"
                    id="feature5"
                    name="feature5"
                    step="0.1"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors duration-200"
                    placeholder="e.g., 80.0"
                    value={formData.feature5}
                    onChange={handleInputChange}
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors duration-200 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Predicting...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5" />
                      <span>Predict</span>
                    </>
                  )}
                </button>
              </form>

              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Sample Values:</h4>
                <p className="text-sm text-gray-600">
                  Flow Duration: 100.5, Packet Count: 50.0, Byte Count: 1024.0, Protocol: 1.0, Port: 80.0
                </p>
              </div>
            </div>
          </motion.div>

          {/* Results */}
          <motion.div variants={itemVariants}>
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">Prediction Results</h3>
              
              {loading && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
                  <span className="ml-3 text-gray-600">Processing your request...</span>
                </div>
              )}

              {error && (
                <div className="flex items-start space-x-3 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-red-800">Error</h4>
                    <p className="text-red-700 text-sm mt-1">{error}</p>
                  </div>
                </div>
              )}

              {result && (
                <div className="space-y-4">
                  <div className="flex items-center space-x-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                    <div>
                      <h4 className="font-medium text-green-800">Prediction Successful</h4>
                      <p className="text-green-700 text-sm">Model processed your input successfully</p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                      <span className="font-medium text-gray-700">Prediction:</span>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        result.is_anomaly || result.label !== 'normal'
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {result.label}
                      </span>
                    </div>

                    {result.anomaly_type && result.anomaly_type !== 'normal' && (
                      <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg border border-red-200">
                        <span className="font-medium text-red-700">Anomaly Type:</span>
                        <span className="px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                          {result.anomaly_type}
                        </span>
                      </div>
                    )}

                    <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                      <span className="font-medium text-gray-700">Confidence:</span>
                      <span className="text-gray-900 font-medium">
                        {(result.score * 100).toFixed(1)}%
                      </span>
                    </div>

                  </div>
                </div>
              )}

              {!loading && !error && !result && (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Play className="w-8 h-8 text-gray-400" />
                  </div>
                  <p className="text-gray-500">Submit your features to see the prediction results</p>
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};

export default TryModel;
