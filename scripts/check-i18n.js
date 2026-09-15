
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const DIRS = ['screens', 'components', 'app', 'i18n'];

function walk(dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, files);
    else if (/\.(js|jsx)$/.test(entry.name)) files.push(full);
  }
  return files;
}

function resolveKey(data, dotted) {
  let node = data;
  for (const part of dotted.split('.')) {
    if (node == null || typeof node !== 'object' || !(part in node)) return undefined;
    node = node[part];
  }
  return typeof node === 'string' ? node : undefined;
}

const locales = {};
for (const lang of ['fr', 'en', 'es', 'ar']) {
  locales[lang] = JSON.parse(
    fs.readFileSync(path.join(ROOT, 'i18n', 'locales', `${lang}.json`), 'utf8')
  );
}

const allFiles = DIRS.flatMap((d) => walk(path.join(ROOT, d)));
const used = new Map(); // key -> file

for (const file of allFiles) {
  const src = fs.readFileSync(file, 'utf8');
  const re = /\bt\(\s*['"`]([^'"`]+)['"`]/g;
  let m;
  while ((m = re.exec(src))) {
    if (!used.has(m[1])) used.set(m[1], path.relative(ROOT, file));
  }
  // cles dynamiques t(`onboarding.${item.key}`) : ignorees, verifiees a la main
}

let missing = 0;
for (const [key, file] of [...used].sort()) {
  for (const [lang, data] of Object.entries(locales)) {
    if (resolveKey(data, key) === undefined) {
      console.log(`MANQUANTE [${lang}] ${key}  (utilisee dans ${file})`);
      missing++;
    }
  }
}

console.log(`\n${used.size} cles uniques verifiees, ${missing} manquante(s).`);
process.exit(missing ? 1 : 0);
