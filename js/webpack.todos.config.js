var path = require('path');
const autoprefixer = require('autoprefixer');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const devMode = process.env.NODE_ENV !== 'production';

var cfg = {
  mode: 'development',
  context: __dirname,
  entry: {
    mdc: [
      './mdc/index.js',
      // './mdc/index.sass',
    ],
  },
  output: {
    path: path.resolve('../src/ryzom_example/todos/static/todos/'),
    filename: 'mdc.js',
  },
  devtool: 'source-map',
  module: {
    rules: [
      { 
        test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: 'url-loader?limit=10000&mimetype=application/font-woff' },
      { 
        test: /\.(ttf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: 'file-loader' },
      {
        test: /\.(sa|sc|c)ss$/,
        use: [
          {
            loader: MiniCssExtractPlugin.loader,
            options: {
              // hmr: process.env.NODE_ENV === 'development',
            },
          },
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
              includePaths: [
                path.resolve('node_modules')
              ],
              sourceMap: true,
            }
          }
        ]
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
    new MiniCssExtractPlugin({
        // Options similar to the same options in webpackOptions.output
        // all options are optional
        filename: '[name].css',
        chunkFilename: '[id].css',
        ignoreOrder: false, // Enable to remove warnings about conflicting order
      }),
  ]
};

module.exports = cfg;
