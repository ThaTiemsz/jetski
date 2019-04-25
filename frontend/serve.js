const proxy = require('http-proxy-middleware');
const Bundler = require('parcel-bundler');
const express = require('express');

const bundler = new Bundler('src/index.html', { cache: false });
const app = express();

app.use('/api', proxy({ target: 'http://0.0.0.0:8686' }));

app.use(bundler.middleware());

app.listen(Number(process.env.PORT || 8080));