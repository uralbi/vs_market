import edge_tts
import asyncio, os

class TT:
    async def playtext(self, text: str, full_filename):
        
        if os.path.exists(full_filename):
            return full_filename
        voice = "ru-RU-DmitryNeural"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(full_filename)
        return full_filename


# Run the async function
if __name__ == "__main__":
    sp = TT()
    txt = """
    Продается 3х комнатная квартира в Районе VEFA центра Кулатова - Элебаева Застройщик - Elite House ЖК - "Континенталь" Комфорт класса Год - 2023 монолит - кирпич Серия - Элитка Площадь - 86м2 Этаж - 3 из 15 Отопление - Центральное Квартира с дизайнерским ремонтом и качественной мебелью Цена: 158.000$ Мини торг !!! Документы: ДДУ. Красная книга.
    """
    asyncio.run(sp.playtext(txt))