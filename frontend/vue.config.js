// vue.config.js
// if able to update Node to v17+, delete the next chunck of code before module.exports
const crypto = require('crypto');

/**
 * The MD4 algorithm is not available anymore in Node.js 17+ (because of library SSL 3).
 * In that case, silently replace MD4 by the MD5 algorithm.
 */
try {
  crypto.createHash('md4');
} catch (e) {
  console.warn('Crypto "MD4" is not supported anymore by this Node.js version');
  const origCreateHash = crypto.createHash;
  crypto.createHash = (alg, opts) => {
    return origCreateHash(alg === 'md4' ? 'md5' : alg, opts);
  };
}
module.exports = {
    publicPath: '/',
    devServer: {
        port: 8080,
        proxy: {
            '/api': {
                target: process.env.VUE_APP_TARGET || 'http://localhost:8000',
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
    },

    // Bundle Optimization
    configureWebpack: {
        optimization: {
            splitChunks: {
                chunks: 'all',
                cacheGroups: {
                    // Vendor chunks - separate large libraries
                    vendor: {
                        test: /[\\/]node_modules[\\/]/,
                        name: 'vendors',
                        priority: 10,
                        reuseExistingChunk: true
                    },
                    // Bootstrap Vue - large library, separate chunk
                    bootstrapVue: {
                        test: /[\\/]node_modules[\\/]bootstrap-vue[\\/]/,
                        name: 'bootstrap-vue',
                        priority: 20,
                        reuseExistingChunk: true
                    },
                    // Moment.js - can be large, separate chunk
                    moment: {
                        test: /[\\/]node_modules[\\/]moment[\\/]/,
                        name: 'moment',
                        priority: 20,
                        reuseExistingChunk: true
                    },
                    // Vue and core libraries
                    vue: {
                        test: /[\\/]node_modules[\\/](vue|vue-router|vuex)[\\/]/,
                        name: 'vue-core',
                        priority: 30,
                        reuseExistingChunk: true
                    },
                    // Common chunk for shared code
                    common: {
                        minChunks: 2,
                        priority: 5,
                        reuseExistingChunk: true
                    }
                }
            }
        }
    },

    // Production optimizations
    productionSourceMap: false,

    css: {
        extract: false,
    },
};
