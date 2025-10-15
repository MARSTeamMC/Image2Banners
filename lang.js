const fs = require("fs");
const path = require("path");

const DEFAULT_LOCALE = "en-US";
const LANG_DIR = "lang";
const CONFIG_FILE = path.join(__dirname, "config.json");
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

    for (const [langCode, remoteUrl] of Object.entries(remoteIndex)) {
        let localData = null;
        if (fs.existsSync(`lang/${langCode}.json`)) {
            const response = await fetch(`lang/${langCode}.json`);
            localData = await response.json();
        }

        console.log(localData)

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

        console.log(remoteLangVersion);
        console.log(localLangVersion);

        if (remoteLangVersion > localLangVersion && remoteAppVersion==localAppVersion) {
            fs.writeFileSync(`lang/${langCode}.json`, JSON.stringify(remoteData, null, 2));
        }
    }
}

async function loadLanguages() {
    const files = fs.readdirSync(LANG_DIR);
    for (const file of files) {
        if (file.endsWith(".json") && file!='index.json') {
            const response = await fetch(`lang/${file}`);
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
    const response = await fetch(`lang/${locale}.json`);
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
