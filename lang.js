const fs = require('fs');
const path = require('path');

const DEFAULT_LOCALE = 'en-US';
const LANG_DIR = 'lang';
const CONFIG_FILE = path.join(__dirname, 'config.json');

let currentLocale = DEFAULT_LOCALE;
if (fs.existsSync(CONFIG_FILE)) {
    const config = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
    if (config.locale) currentLocale = config.locale;
}

setLanguage(currentLocale);

async function setLanguage(locale) {
    const response = await fetch(`lang/${locale}.json`);
    const translation = await response.json();
    const translationKeys = Object.keys(translation);
    for (const translationKey of translationKeys) {
        document.getElementById(translationKey).textContent = translation[translationKey];
    }

    fs.writeFileSync(CONFIG_FILE, JSON.stringify({ locale }, null, 2), 'utf8');
}