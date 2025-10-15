const fs = require("fs");
const path = require("path");

const DEFAULT_LOCALE = "en-US";
const LANG_DIR = path.join(__dirname, "lang");
const CONFIG_FILE = path.join(__dirname, "config.json");
const PACKAGE_FILE = path.join(__dirname, "package.json");
const REMOTE_INDEX_URL = 'https://raw.githubusercontent.com/MARSTeamMC/Image2Banners/main/lang/index.json';

let currentLocale = DEFAULT_LOCALE;
if (fs.existsSync(CONFIG_FILE)) {
    const config = JSON.parse(fs.readFileSync(CONFIG_FILE, "utf8"));
    if (config.locale) currentLocale = config.locale;
}

updateLanguages().then(() => {
    loadLanguages();
    setLanguage(currentLocale);
});

async function updateLanguages() {
    try {
        const res = await fetch(REMOTE_INDEX_URL);
    if (!res.ok) throw new Error(res.statusText);
        remoteIndex = await res.json();
    } catch (err) {
        console.log("No remote translation index found or network offline.");
        return;
    }

    console.log(LANG_DIR);

    for (const [langCode, remoteUrl] of Object.entries(remoteIndex)) {
        let localData = null;
        if (fs.existsSync(`${LANG_DIR}/${langCode}.json`)) {
            const response = await fetch(`${LANG_DIR}/${langCode}.json`);
            localData = await response.json();
        }

        let remoteData;
        try {
            const res = await fetch(remoteUrl);
            if (!res.ok) continue;
            remoteData = await res.json();
        } catch {
            continue;
        }

        let localAppVersion = "0.0.0";
        let localLangVersion = 0;
        if (localData!=null) {
            localAppVersion = localData["appVersion"];
            localLangVersion = localData["langVersion"];
        }

        remoteAppVersion = remoteData["appVersion"];
        remoteLangVersion = remoteData["langVersion"];

        const app_response = await fetch(PACKAGE_FILE);
        package = await app_response.json();

        if ((remoteLangVersion > localLangVersion && remoteAppVersion==localAppVersion) || (localData == null && remoteAppVersion==package["version"])) {
            fs.writeFileSync(`${LANG_DIR}/${langCode}.json`, JSON.stringify(remoteData, null, 2));
        }
    }
}

async function loadLanguages() {
    const files = fs.readdirSync(LANG_DIR);
    for (const file of files) {
        if (file.endsWith(".json") && file!='index.json') {
            const response = await fetch(`${LANG_DIR}/${file}`);
            const translation = await response.json();
            const languageName = translation["languageName"];
            const translators = translation["translators"].join(", ");

            let div = document.querySelectorAll('.dropdown-content')[0];
            let button = document.createElement("button");
            button.classList.add("button");
            button.style.marginTop = "8px";
            button.dataset.lang = file.split(".")[0];
            button.onclick = function() {
              setLanguage(this.dataset.lang);
            };
            button.innerHTML  = `${languageName} <br> (by ${translators})`;
            div.appendChild(button)
        }
    }
}

async function setLanguage(locale) {
    const response = await fetch(`${LANG_DIR}/${locale}.json`);
    const translation = await response.json();
    const translationKeys = Object.keys(translation);
    for (const translationKey of translationKeys) {
        try {
            document.getElementById(translationKey).textContent = translation[translationKey];
        } catch (e) {
            console.log("Caught error:", e.message);
        }
    }

    fs.writeFileSync(CONFIG_FILE, JSON.stringify({ locale }, null, 2), "utf8");
}
