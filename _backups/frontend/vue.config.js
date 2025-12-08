// vue.config.js
module.exports = {
    devServer: {
        // host: 'localhost',
        // host: '127.0.0.1',
        // host: '0.0.0.0',
        // port: 8080,
        // public: 'localhost:8080',
        proxy: {
            '/api/*': {
                target: process.env.VUE_APP_TARGET,
                secure: false,
                changeOrigin: true
            }
        }
    },

    pluginOptions: {
      moment: {
        locales: [
          ''
        ]
      }
    }
};
