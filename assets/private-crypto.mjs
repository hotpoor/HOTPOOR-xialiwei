const encoder=new TextEncoder();
export const iterations=600000;
function bytes(value) {
  if (typeof value!=='string' || !/^[A-Za-z0-9_-]+$/.test(value)) throw Error('Invalid encoding');
  return Uint8Array.from(atob(value.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
}
function encoded(value) {
  let text=''; for(const b of new Uint8Array(value)) text+=String.fromCharCode(b);
  return btoa(text).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/g,'');
}
function validId(id) { if(!/^[a-z0-9-]+$/.test(id)) throw Error('Invalid record ID'); }
async function derive(password,salt,api,usage) {
  if(typeof password!=='string' || !password || password.length>4096) throw Error('Invalid password');
  const input=encoder.encode(password);
  let material;
  try {material=await api.subtle.importKey('raw',input,'PBKDF2',false,['deriveKey']);} finally {input.fill(0);}
  return api.subtle.deriveKey({name:'PBKDF2',salt,iterations,hash:'SHA-256'},material,{name:'AES-GCM',length:256},false,[usage]);
}
export async function encryptRecord(text,password,id,api=globalThis.crypto) {
  validId(id);
  if(password.length<12) throw Error('Use at least 12 characters');
  const salt=api.getRandomValues(new Uint8Array(16)),iv=api.getRandomValues(new Uint8Array(12));
  const key=await derive(password,salt,api,'encrypt');
  const plain=encoder.encode(text);
  try {
    const ciphertext=await api.subtle.encrypt({name:'AES-GCM',iv,tagLength:128,additionalData:encoder.encode(`HOTPOOR-XIALIWEI|v1|${id}`)},key,plain);
    return {version:1,algorithm:'AES-256-GCM',kdf:'PBKDF2-SHA256',iterations,id,salt:encoded(salt),iv:encoded(iv),ciphertext:encoded(ciphertext)};
  } finally {plain.fill(0);}
}
export async function decryptRecord(envelope,password,expectedId,api=globalThis.crypto) {
  validId(expectedId);
  if(envelope.version!==1 || envelope.algorithm!=='AES-256-GCM' || envelope.kdf!=='PBKDF2-SHA256' || envelope.iterations!==iterations || envelope.id!==expectedId) throw Error('Unsupported record');
  const salt=bytes(envelope.salt),iv=bytes(envelope.iv);
  if(salt.length!==16 || iv.length!==12) throw Error('Invalid salt or nonce');
  const key=await derive(password,salt,api,'decrypt');
  const plain=await api.subtle.decrypt({name:'AES-GCM',iv,tagLength:128,additionalData:encoder.encode(`HOTPOOR-XIALIWEI|v1|${expectedId}`)},key,bytes(envelope.ciphertext));
  const data=new Uint8Array(plain);
  try {return new TextDecoder('utf-8',{fatal:true}).decode(data);} finally {data.fill(0);}
}
