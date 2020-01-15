var path = require('path');
const autoprefixer = require('autoprefixer');
const ExtractTextPlugin = require('extract-text-webpack-plugin');

const extractSass = new ExtractTextPlugin({
  filename: 'ryzom.css',
});

var cfg = {
  mode: 'development',
  entry: {
    main: [
      './index.js',
      './style.scss',
    ],
  },
  output: {
    path: path.resolve(__dirname, '../ryzom/static'),
    filename: 'ryzom.js',
  },
  devtool: 'source-map',
//   entry: './webpack_entry.py',
//   output: {
//     filename: 'todos.js',
//     path: path.resolve(__dirname, 'todos/static')
//   },  
  module: {
    rules: [
      { 
        test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: 'url-loader?limit=10000&mimetype=application/font-woff' },
      { 
        test: /\.(ttf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: 'file-loader' },
      {
        test: /\.s(a|c)ss$/,
        use: extractSass.extract({
          use: [
            {
              loader: 'css-loader',
              options: {
                sourceMap: true
              }
            },
            {
              loader: 'postcss-loader',
              options: {
                sourceMap: true,
                plugins: () => [autoprefixer({grid: false})]
              }
            },
            {
              loader: 'sass-loader',
              options: {
                sourceMap: true,
                includePaths: [
                  path.resolve(__dirname, 'node_modules')
                ]
              }
            }
          ]
        })
      }
    ]
  },
  plugins: [
    extractSass
  ]
};

module.exports = cfg;
