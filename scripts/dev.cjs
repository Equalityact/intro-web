'use strict';
// Absolute paths work in PowerShell, cmd.exe, macOS and Linux.
const path = require('node:path');
require('live-server').start({
  root: path.join(__dirname, '..', 'public'),
  port: Number(process.env.PORT) || 3000,
  open: false,
  middleware: [require('./clean-urls')],
});
