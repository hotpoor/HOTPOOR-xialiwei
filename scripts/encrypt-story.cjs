'use strict';
const fs = require('node:fs');
const path = require('node:path');
const {randomBytes, createCipheriv, createDecipheriv, pbkdf2Sync} = require('node:crypto');
const root = path.resolve(__dirname, '..');
const aad = id => Buffer.from(`HOTPOOR-XIALIWEI|v1|${id}`, 'utf8');
function validateId(id) { if (!/^[a-z0-9-]+$/.test(id)) throw Error('Invalid record ID'); }
function encrypt(text, id, password) {
  validateId(id);
  if(typeof password!=='string' || password.length<12) throw Error('Use at least 12 characters');
  const salt=randomBytes(16),key=pbkdf2Sync(password,salt,600000,32,'sha256');
  const iv = randomBytes(12), cipher = createCipheriv('aes-256-gcm', key, iv);
  cipher.setAAD(aad(id));
  const data = Buffer.concat([cipher.update(text, 'utf8'), cipher.final(), cipher.getAuthTag()]);
  key.fill(0);
  return {version:1, algorithm:'AES-256-GCM', kdf:'PBKDF2-SHA256', iterations:600000, id, salt:salt.toString('base64url'), iv:iv.toString('base64url'), ciphertext:data.toString('base64url')};
}
function decrypt(envelope, password) {
  validateId(envelope.id);
  if (envelope.version !== 1 || envelope.algorithm !== 'AES-256-GCM' || envelope.kdf!=='PBKDF2-SHA256' || envelope.iterations!==600000) throw Error('Unsupported format');
  const key=pbkdf2Sync(password,Buffer.from(envelope.salt,'base64url'),600000,32,'sha256');
  const data = Buffer.from(envelope.ciphertext, 'base64url');
  const cipher = createDecipheriv('aes-256-gcm', key, Buffer.from(envelope.iv, 'base64url'));
  cipher.setAAD(aad(envelope.id)); cipher.setAuthTag(data.subarray(-16));
  try {return Buffer.concat([cipher.update(data.subarray(0,-16)), cipher.final()]).toString('utf8');}
  finally {key.fill(0);}
}
function outsideRepo(file) {
  const resolved = fs.existsSync(file) ? fs.realpathSync(file) : path.join(fs.realpathSync(path.dirname(file)), path.basename(file));
  const relative = path.relative(root, resolved);
  if (!relative || (!relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative))) throw Error('Private files must be outside the repository');
}
if (require.main === module) {
  const [id, input, output, keyFile] = process.argv.slice(2);
  if (!keyFile) throw Error('Usage: node scripts/encrypt-story.cjs ID PRIVATE_INPUT PUBLIC_OUTPUT PRIVATE_KEY_FILE');
  validateId(id); outsideRepo(input); outsideRepo(keyFile);
  if (fs.existsSync(output)) throw Error('Refusing to overwrite an existing envelope');
  const text = fs.readFileSync(input, 'utf8'), password = fs.readFileSync(keyFile,'utf8').replace(/\r?\n$/,'');
  const envelope = encrypt(text, id, password);
  if (decrypt(envelope,password) !== text) throw Error('Round-trip verification failed');
  fs.writeFileSync(output, JSON.stringify(envelope,null,2)+'\n', {flag:'wx'});
  console.log('Encrypted record written and round-trip verified. Key not displayed.');
}
module.exports = {encrypt,decrypt,outsideRepo};
