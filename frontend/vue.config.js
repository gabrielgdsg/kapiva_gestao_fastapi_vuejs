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
