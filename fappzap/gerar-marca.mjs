// Gera os PNGs da marca FappZap Acesso a partir de fappzap/icone-acesso.svg.
// Roda na máquina de quem mexe no ícone (precisa do sharp), não no CI: o resultado fica
// commitado em fappzap/marca/, espelhando o caminho de destino no repositório.
//   NODE_PATH=<pasta com sharp> node fappzap/gerar-marca.mjs && python fappzap/gerar-ico.py
import { createRequire } from 'node:module';
import { mkdirSync, readFileSync, writeFileSync, copyFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

// createRequire respeita o NODE_PATH (o import de ESM não).
const sharp = createRequire(import.meta.url)('sharp');

const AQUI = dirname(fileURLToPath(import.meta.url));
const MARCA = join(AQUI, 'marca');
const svg = readFileSync(join(AQUI, 'icone-acesso.svg'), 'utf8');

// Ícone adaptativo do Android: o fundo vira a cor do launcher e o desenho entra a 70%,
// senão a máscara redonda do launcher corta o selo (lição dos APKs do FappZap, 1.138.0).
const corpo = svg.replace(/<rect x="16" y="16" width="480" height="480" rx="112" fill="url\(#fundo\)"\/>/, '');
const frente = corpo
  .replace(/(<\/defs>)/, '$1<g transform="translate(256 256) scale(0.7) translate(-256 -256)">')
  .replace(/<\/svg>\s*$/, '</g></svg>');
// Silhueta branca do "F" para a notificação do Android (o sistema só usa o alfa).
const silhueta = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <path d="M156 70h214v70H240v62h118v68H240v172h-84z" fill="#fff"/></svg>`;

const png = async (fonte, tam, destino, redondo = false) => {
  const p = join(MARCA, destino);
  mkdirSync(dirname(p), { recursive: true });
  let img = sharp(Buffer.from(fonte), { density: 384 }).resize(tam, tam);
  if (redondo) {
    const mascara = Buffer.from(`<svg width="${tam}" height="${tam}"><circle cx="${tam / 2}" cy="${tam / 2}" r="${tam / 2}" fill="#fff"/></svg>`);
    img = sharp(await img.png().toBuffer()).composite([{ input: mascara, blend: 'dest-in' }]);
  }
  await img.png().toFile(p);
};

await png(svg, 1024, 'res/icon.png');
await png(svg, 512, 'flutter/assets/icon.png');
for (const [t, n] of [[32, '32x32'], [64, '64x64'], [128, '128x128'], [256, '128x128@2x']]) await png(svg, t, `res/${n}.png`);
for (const t of [16, 24, 32, 48, 64, 128, 256]) await png(svg, t, `../ico-fontes/${t}.png`);

const dens = { mdpi: 1, hdpi: 1.5, xhdpi: 2, xxhdpi: 3, xxxhdpi: 4 };
for (const [d, f] of Object.entries(dens)) {
  const base = `flutter/android/app/src/main/res/mipmap-${d}`;
  await png(svg, 48 * f, `${base}/ic_launcher.png`);
  await png(svg, 48 * f, `${base}/ic_launcher_round.png`, true);
  await png(frente, 108 * f, `${base}/ic_launcher_foreground.png`);
  await png(silhueta, 24 * f, `${base}/ic_stat_logo.png`);
}

// Rótulo do instalador portátil (96×32): o ícone à esquerda, fundo transparente.
const rotulo = join(MARCA, 'libs/portable/src/res/label.png');
mkdirSync(dirname(rotulo), { recursive: true });
await sharp({ create: { width: 96, height: 32, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } })
  .composite([{ input: await sharp(Buffer.from(svg), { density: 384 }).resize(32, 32).png().toBuffer(), left: 0, top: 0 }])
  .png().toFile(rotulo);

mkdirSync(join(MARCA, 'flutter/assets'), { recursive: true });
copyFileSync(join(AQUI, 'icone-acesso.svg'), join(MARCA, 'flutter/assets/icon.svg'));
mkdirSync(join(MARCA, 'res'), { recursive: true });
copyFileSync(join(AQUI, 'icone-acesso.svg'), join(MARCA, 'res/scalable.svg'));
writeFileSync(join(MARCA, '.gerado'), 'gerado por fappzap/gerar-marca.mjs a partir de icone-acesso.svg\n');
console.log('marca gerada em', MARCA);
