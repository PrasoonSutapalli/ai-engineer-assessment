"""
Indonesia Native-Language Voice Agent (Multifinance & Consumer Loan Reminder).
Handles formal & colloquial Bahasa Indonesia, finance loanwords (cicilan, tenor, denda, DP, jatuh tempo),
regional conversational nuances (East Java / Javanese colloquial registers), and escalation.
"""

import re
import uuid
from typing import Dict, Any, List, Optional


class IndonesiaMultifinanceBot:
    """
    Multifinance Installment Reminder & Loan Follow-up Voice Agent for Indonesia.
    Supports regional colloquial markers, polite honorifics (Pak/Bu/Mas/Mbak), and finance terms.
    """

    def __init__(self, customer_name: str = "Bapak Hendra", finance_company: str = "Aegis Multifinance"):
        self.call_id = str(uuid.uuid4())
        self.customer_name = customer_name
        self.finance_company = finance_company
        self.state = "GREETING"
        self.history: List[Dict[str, str]] = []
        self.escalated = False

    def process_turn(self, user_input: str) -> Dict[str, Any]:
        """Processes conversational turns in Indonesian with loanword and regional dialect support."""
        self.history.append({"speaker": "CUSTOMER", "text": user_input})
        text = user_input.lower()
        action_executed = None

        # 1. Human Escalation Triggers (Indonesian & Javanese colloquial)
        escalate_triggers = [
            'manusia', 'bicara dengan staf', 'bicara sama orang', 'supervisor', 'operator',
            'ngomong sama orang', 'staf finance', 'petugas', 'sambungkan', 'agen'
        ]
        if any(trig in text for trig in escalate_triggers):
            self.escalated = True
            self.state = "ESCALATED"
            speech = (
                f"Baik, {self.customer_name}. Saya sambungkan langsung ke Tim Petugas Pembiayaan kami "
                f"untuk membantu solusi kendala pembayaran Bapak. Mohon ditunggu sebentar ya Pak."
            )
            action_executed = {"task": "ESCALATE_TO_ID_MULTIFINANCE_AGENT", "market": "ID", "language": "Indonesian"}
            self.history.append({"speaker": "AGENT", "text": speech})
            return {"speech_text": speech, "state": self.state, "escalated": True, "action": action_executed}

        # 2. Penalty & Dispute Handling (Denda / Keringanan / Jatuh Tempo)
        if any(w in text for w in ['denda', 'keringanan', 'potong', 'mahal', 'keberatan', 'ndak bisa bayar denda']):
            speech = (
                f"Untuk rincian denda keterlambatan sebesar Rp 150.000, jika {self.customer_name} melakukan pelunasan "
                f"pokok angsuran hari ini sebelum pukul 17.00 WIB melalui Virtual Account BCA atau Alfamart, "
                f"kami bisa ajukan program penghapusan denda 50%. Apakah berkenan Pak?"
            )
            self.state = "OFFERED_FINE_DISCOUNT"
        elif any(w in text for w in ['virtual account', 'bayar lewat mana', 'cara bayar', 'transfer', 'va', 'alfamart', 'indomaret']):
            speech = (
                f"Pembayaran cicilan sangat mudah Pak. Bisa transfer ke BCA Virtual Account 8829-0812-3456 atau langsung tunai "
                f"di kasir Indomaret/Alfamart terdekat cukup sebutkan nomor kontrak pembiayaan Bapak."
            )
            self.state = "EXPLAINED_PAYMENT_CHANNEL"
        elif any(w in text for w in ['tenor', 'perpanjang', 'restrukturisasi', 'cicilan', 'angsuran']):
            speech = (
                f"Angsuran bulanan {self.customer_name} adalah sebesar Rp 1.450.000 dengan sisa tenor 12 bulan. "
                f"Tersedia juga opsi restrukturisasi perpanjangan tenor hingga 24 bulan agar cicilan lebih ringan."
            )
            self.state = "EXPLAINED_TENOR"
        elif self.state == "GREETING":
            if any(w in text for w in ['ya', 'iya', 'nggih', 'betul', 'bisa', 'halo', 'monggo', 'ada apa']):
                speech = (
                    f"Terima kasih {self.customer_name}. Kami ingin mengonfirmasi bahwa angsuran pembiayaan motor Honda Vario "
                    f"Bapak sebesar Rp 1.450.000 akan jatuh tempo besok tanggal 20. Apakah pembayarannya sudah dijadwalkan Pak?"
                )
                self.state = "CONFIRMING_DUE_DATE"
            else:
                speech = f"Terima kasih {self.customer_name}, selamat beraktivitas kembali dan semoga sehat selalu."
                self.state = "COMPLETED"
        elif self.state in ["CONFIRMING_DUE_DATE", "OFFERED_FINE_DISCOUNT"]:
            if any(w in text for w in ['sudah', 'nanti sore', 'sekarang', 'nggih', 'siap', 'mau bayar', 'oke']):
                speech = (
                    f"Alhamdulillah, terima kasih banyak atas kerjasamanya {self.customer_name}. Bukti pembayaran akan otomatis "
                    f"terverifikasi di sistem kami via SMS dan WhatsApp resmi. Matur nuwun dan selamat siang Pak."
                )
                self.state = "PROMISE_TO_PAY_LOGGED"
                action_executed = {"task": "LOG_PROMISE_TO_PAY", "status": "CONFIRMED", "amount_idr": 1450000}
            else:
                speech = f"Ada yang bisa kami bantu jelaskan terkait jadwal atau metode pembayaran angsuran Bapak?"
        else:
            speech = f"Terima kasih {self.customer_name}, kami siap melayani informasi pembiayaan Bapak."

        self.history.append({"speaker": "AGENT", "text": speech})
        return {
            "speech_text": speech,
            "state": self.state,
            "escalated": self.escalated,
            "action": action_executed
        }
