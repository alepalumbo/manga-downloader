"""
App Kivy - Manga Downloader
Scarica capitoli manga da URL e li converte in PDF.

Dipendenze:
    pip install kivy requests pillow
"""

import os
import threading
from io import BytesIO

import requests
from PIL import Image

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp


# ─────────────────────────────────────────────
#  Logica di download (identica allo script PC)
# ─────────────────────────────────────────────

def scarica_capitolo(primo_url: str, cartella_output: str, log_callback, fine_callback):
    """Scarica le immagini e crea il PDF. Gira in un thread separato."""

    def log(msg):
        Clock.schedule_once(lambda dt: log_callback(msg))

    try:
        base_url = primo_url.rsplit("/", 1)[0] + "/"
        nome_file = primo_url.rsplit("/", 1)[1]
        ext = os.path.splitext(nome_file)[1]
        n_cifre = len(os.path.splitext(nome_file)[0])
        capitolo = primo_url.rstrip("/").rsplit("/", 2)[-2]

        os.makedirs(cartella_output, exist_ok=True)
        log(f"📂 Cartella: {cartella_output}")
        log(f"🔗 Base URL: {base_url}")
        log("🔍 Scarico le immagini...\n")

        sessione = requests.Session()
        sessione.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": base_url,
        })

        immagini_pil = []
        numero = 1

        while True:
            nome = str(numero).zfill(n_cifre) + ext
            url = base_url + nome

            try:
                risposta = sessione.get(url, timeout=10)
                if risposta.status_code != 200:
                    log(f"✅ Fine al file {nome}")
                    break

                content_type = risposta.headers.get("Content-Type", "")
                if "image" not in content_type:
                    log(f"✅ Fine al file {nome} (non immagine)")
                    break

                img = Image.open(BytesIO(risposta.content)).convert("RGB")
                immagini_pil.append(img)
                log(f"  ✔ Scaricata: {nome}")
                numero += 1

            except requests.exceptions.RequestException as e:
                log(f"⚠️ Errore su {nome}: {e}")
                break

        if not immagini_pil:
            log("❌ Nessuna immagine scaricata. Controlla l'URL.")
            Clock.schedule_once(lambda dt: fine_callback(False))
            return

        pdf_path = os.path.join(cartella_output, f"capitolo_{capitolo}.pdf")
        prima = immagini_pil[0]
        resto = immagini_pil[1:]
        prima.save(pdf_path, save_all=True, append_images=resto)

        log(f"\n📄 PDF creato: {pdf_path}")
        log(f"📊 Pagine totali: {len(immagini_pil)}")
        Clock.schedule_once(lambda dt: fine_callback(True))

    except Exception as e:
        log(f"❌ Errore inatteso: {e}")
        Clock.schedule_once(lambda dt: fine_callback(False))


# ─────────────────────────────────────────────
#  UI Kivy
# ─────────────────────────────────────────────

class MangaDownloaderApp(App):

    def build(self):
        self.title = "Manga Downloader"
        self.cartella_scelta = self._cartella_default()

        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))

        # ── URL input ──
        root.add_widget(Label(
            text="URL prima immagine (es. .../01.jpg)",
            size_hint_y=None, height=dp(30),
            halign="left", text_size=(None, None)
        ))

        self.url_input = TextInput(
            hint_text="https://onepiecepower.com/.../01.jpg",
            size_hint_y=None, height=dp(50),
            multiline=False
        )
        root.add_widget(self.url_input)

        # ── Cartella output ──
        root.add_widget(Label(
            text="Cartella di output:",
            size_hint_y=None, height=dp(25),
            halign="left"
        ))

        cartella_row = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))

        self.cartella_label = Label(
            text=self.cartella_scelta,
            halign="left",
            text_size=(None, None),
            size_hint_x=0.75
        )
        cartella_row.add_widget(self.cartella_label)

        btn_sfoglia = Button(
            text="Sfoglia",
            size_hint_x=0.25
        )
        btn_sfoglia.bind(on_press=self.apri_file_chooser)
        cartella_row.add_widget(btn_sfoglia)

        root.add_widget(cartella_row)

        # ── Bottone download ──
        self.btn_download = Button(
            text="⬇ Scarica e crea PDF",
            size_hint_y=None, height=dp(55),
            background_color=(0.2, 0.6, 1, 1)
        )
        self.btn_download.bind(on_press=self.avvia_download)
        root.add_widget(self.btn_download)

        # ── Log scrollabile ──
        root.add_widget(Label(
            text="Log:",
            size_hint_y=None, height=dp(25),
            halign="left"
        ))

        scroll = ScrollView()
        self.log_label = Label(
            text="In attesa...\n",
            size_hint_y=None,
            halign="left",
            valign="top",
            text_size=(None, None),
            markup=True
        )
        self.log_label.bind(texture_size=lambda inst, val: setattr(inst, "size", val))
        scroll.add_widget(self.log_label)
        root.add_widget(scroll)

        return root

    # ── Helpers ──

    def _cartella_default(self):
        """Cartella Download su Android o Desktop su PC."""
        if os.path.exists("/sdcard/Download"):
            return "/sdcard/Download"
        return os.path.join(os.path.expanduser("~"), "Downloads")

    def aggiungi_log(self, testo):
        self.log_label.text += testo + "\n"

    def apri_file_chooser(self, instance):
        content = BoxLayout(orientation="vertical", spacing=dp(8))

        fc = FileChooserListView(
            path=self.cartella_scelta,
            dirselect=True,         # seleziona cartelle
            filters=[""],
        )
        content.add_widget(fc)

        bottoni = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))

        btn_ok = Button(text="Scegli")
        btn_annulla = Button(text="Annulla")
        bottoni.add_widget(btn_ok)
        bottoni.add_widget(btn_annulla)
        content.add_widget(bottoni)

        popup = Popup(title="Scegli cartella", content=content, size_hint=(0.95, 0.85))

        def conferma(inst):
            if fc.selection:
                self.cartella_scelta = fc.selection[0]
            else:
                self.cartella_scelta = fc.path
            self.cartella_label.text = self.cartella_scelta
            popup.dismiss()

        btn_ok.bind(on_press=conferma)
        btn_annulla.bind(on_press=popup.dismiss)
        popup.open()

    def avvia_download(self, instance):
        url = self.url_input.text.strip()

        if not url or not url.startswith("http"):
            self.aggiungi_log("❌ Inserisci un URL valido!")
            return

        # Disabilita il bottone durante il download
        self.btn_download.disabled = True
        self.btn_download.text = "⏳ Download in corso..."
        self.log_label.text = ""

        def fine(successo):
            self.btn_download.disabled = False
            self.btn_download.text = "⬇ Scarica e crea PDF"
            if successo:
                self.aggiungi_log("\n🎉 Completato!")

        thread = threading.Thread(
            target=scarica_capitolo,
            args=(url, self.cartella_scelta, self.aggiungi_log, fine),
            daemon=True
        )
        thread.start()


if __name__ == "__main__":
    MangaDownloaderApp().run()
