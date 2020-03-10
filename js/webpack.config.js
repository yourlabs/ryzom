var path = require('path');
const autoprefixer = require('autoprefixer');
const ExtractTextPlugin = require('extract-text-webpack-plugin');

const extractSass = new ExtractTextPlugin({
  filename: 'ryzom_ex.css',
});

var cfg = {
  mode: 'development',
  context: __dirname,
  entry: {
    main: [
      './index.js',
      './style.scss',
    ],
  },
  output: {
    path: path.resolve('../src/ryzom_example/ryz_ex/static/ryz_ex/'),
    filename: 'ryzom_ex.js',
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
                sassOptions: {
                    includePaths: [
                      path.resolve('node_modules')
                    ]
                }
              }
            }
          ]
        })
      },
      {
      	test: /\.py$/,
          loader: 'py-loader',
          options: {
            compiler: 'transcrypt'
          }
        },
    ]
  },
  plugins: [
    extractSass
  ]
};

module.exports = cfg;
