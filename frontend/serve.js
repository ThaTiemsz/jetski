const proxy = require('http-proxy-middleware');
const Bundler = require('parcel-bundler');
const express = require('express');

const bundler = new Bundler(['./src/index.html', '../rowboat/templates/archive.html'], { cache: false });
const app = express();

app.use('/api', proxy({ target: 'http://web:8686' }));

app.use(bundler.middleware());

app.listen(Number(process.env.PORT || 8080));