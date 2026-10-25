# VINYL v0.4 — patch pro InterTune

**Co je hotovo:** nový Kotlin/Jetpack Compose komponent `VinylDisc.kt` (vinyl s drážkami, obalem alba, středovým otvorem, animací 33 rpm), `apply_vinyl.py` pro bezpečné vložení do aktuálního InterTune přehrávače a GitHub Actions workflow, které stáhne zdroj InterTune a sestaví APK.

**Co stále není hotovo:** nemáme odzkoušenou kompilaci APK ani chování na Motorole. InterTune se v tomto balíčku nenachází — workflow ho stáhne na GitHubu. Zamčenou obrazovku zatím řeší samostatný experimentální VINYL Live Companion, nejde o součást tohoto forku. Zdroj YouTube Music i jeho možná omezení zůstávají původní z InterTune.

## Jak postavit APK pouze pomocí mobilu

1. Na GitHubu vytvoř nový repozitář, např. `vinyl-intertune`.
2. Nahraj **obsah této složky** do kořene repozitáře, včetně skryté `.github/workflows/build-vinyl.yml` (ne samotný ZIP). Na mobilu může pomoct GitHub Codespaces: rozbal ZIP do repozitáře, commitni a pushni.
3. Otevři **Actions → Build VINYL from InterTune → Run workflow**; případně se spustí při `push` do `main`/`master`.
4. Při úspěšném buildu otevři běh workflow a stáhni artefakt **VINYL-InterTune-debug-APK**. Rozbal ho a nainstaluj APK na Motorolu.
5. Pusť skladbu. Obal se zobrazí jako gramofonová deska; přehrávání = rotace, pauza = stop. **Dlouhým stiskem obalu** lze režim přepnout mezi vinylem a původním obalem. Volba zůstane uložena.

## Významné vlastnosti a omezení

- Využívá fungující přehrávač a katalog **InterTune**; kopírování funkcí všech konkurenčních aplikací tímto není provedeno.
- Deska se točí jen pokud je viditelná v UI a běží aktivní přehrávání. Dřívější live wallpaper je samostatná věc.
- 33 rpm (přibližně 1,818 s/otáčku), při pauze si zachová úhel; bez vlastní síťové komunikace.
- Patch používá konkrétní strukturu `visionos-fix` větve z 25. 10. 2026. Až se upstream změní, patch raději skončí s chybou než poškodí soubory.
- APK je podepsané **debug podpisem** pro testování a není připravené k veřejné distribuci.
- Technicky je potřeba Java 21, Android SDK 36, NDK 29.0.13113456, CMake 3.31.6 a submoduly InterTune.
- GPL-3.0-only: při distribuci upravené aplikace zachovej autorská upozornění, licenci a nabídni odpovídající zdrojový kód včetně úprav. Neoznačuj fork za oficiální InterTune.

Zdroj InterTune: https://github.com/ItzSkyeYT/InterTune
Zdroj SimpMusic (v tomto balíčku není): https://github.com/maxrave-dev/SimpMusic

- Fork má vlastní ID `cz.vinyl.intertune.debug` a popisek **VINYL**, takže by se neměl přepisovat oficiální InterTune. Ostatní ID třetích stran v upstream kódu vyžadují reálný test.
