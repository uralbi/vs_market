import re
from bs4 import BeautifulSoup
import requests
from io import BytesIO
import time
from datetime import datetime, timedelta


def is_within_days(date_str, lapse_days=3):
    
    # Example date format: "13 Февраль 2025 - 12:43, Сегодня, 10:44"
    
    if "Сегодня" in date_str:
        return True
    month_map = {
        "Январь": "January", "Февраль": "February", "Март": "March",
        "Апрель": "April", "Май": "May", "Июнь": "June",
        "Июль": "July", "Август": "August", "Сентябрь": "September",
        "Октябрь": "October", "Ноябрь": "November", "Декабрь": "December"
    }

    date_part, time_part = date_str.split(" - ")  # Correctly split date & time
    day, ru_month, year = date_part.split(" ")  # Extract day, month, year
    month = month_map[ru_month]
    formatted_date = f"{day} {month} {year} {time_part}"
    date_obj = datetime.strptime(formatted_date, "%d %B %Y %H:%M")
    time_limit = datetime.now() - timedelta(days=lapse_days)
    return date_obj >= time_limit


class Client:
    
    def __init__(self, email_s, pass_s, topic='283', items_qty = 5):
        self.email = email_s
        self.password = pass_s
        self.access_token = ''
        self.refresh_token = ''
        self.topic = topic
        self.qty = items_qty
        # self.domain = "http://127.0.0.1:8000"
        self.domain = "https://ai-ber.com"
    
    def get_access(self):
        url = f"{self.domain}/api/auth/token"
        data = {"email": self.email, "password": self.password}
        response = requests.post(url, json=data)
        data = response.json()
        if str(response.status_code) == "200":
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            return True
        else:
            return False
    
    def request_data(self):
        ds = DiesBot(self.topic)
        links = ds.get_links()
        r = 0
        datas = []
        for link in links:
            data = ds.get_data(link)
            if data:
                datas.append(data)
                r+=1
                print('datas: r:', r)
            if r >= self.qty + 3:
                break
        return datas
    
    def post_item(self):
        datas = self.request_data()
        res = 0
        for data in datas:
            try:
                recent = is_within_days(data["published"], 2)
                if not recent:
                    print('Not recent data')
                    continue
            except Exception as e:
                print(e)
            if data["currency"] != 'Com':
                is_doll = 'true'
            else:
                is_doll = 'false'
            url = f"{self.domain}/api/products/create"
            form_data = {
                "name": data['title'],
                "description": data['info'],
                "price": data['price'],
                "is_dollar": is_doll,  # Boolean fields must be sent as strings
                "activated": "true",
                "category": topics[self.topic],    # need to update!
            }

            image_urls = data["images"][:4]
            
            files = []
            for idx, img_url in enumerate(image_urls):
                img_response = requests.get(img_url, stream=True)
                if img_response.status_code == 200:
                    image_file = BytesIO(img_response.content)  # Convert to file-like object
                    files.append(("images", (f"image{idx+1}.jpg", image_file, "image/jpeg")))
            
            if not files:
                print("❌ No images were added to the request.")
                continue

            headers = {"Authorization": f"Bearer {self.access_token}"}
            time.sleep(1)
            response = requests.post(url, data=form_data, files=files, headers=headers)
            if response.status_code == 200:
                pass
            else:
                print(f"Error {response.status_code}: {response.text}")
            res+=1
            if res >= self.qty:
                break
        return res
    
    def run(self):
        if self.get_access():
            rs= self.post_item()
            print(f"Posted {rs} items")
            


class DiesBot:

    def __init__(self, forum):
        self.forum = forum
        self.source1 = requests.get(f'https://diesel.elcat.kg/index.php?showforum={self.forum}').text
        self.soup1 = BeautifulSoup(self.source1, 'lxml')

    def get_links(self):
        urls1 = self.soup1.find_all('a', href=True)
        url_list1 = [url['href'] for url in urls1]
        link2 = []
        for link in url_list1:
            if len(link) == 88:
                if link not in link2:
                    link2.append(link)
        return link2

    def get_maintext(self, dlink):
        source = requests.get(dlink).text
        soup = BeautifulSoup(source, 'lxml')
        theme_org = soup.find('h1', class_="ipsType_pagetitle").text
        if "[Правила]" in theme_org:
            return None
        theme = self.remove_phone_in_title(theme_org)
        theme = theme.strip().replace('  ', ' ')
        theme = self.clean_title(theme)
        try:
            text = soup.find_all("div", {"class": "custom-field"})
            maintext_1 = ''
            for item in text:
                maintext_1 += item.text
            form_fields = self.format_fields(maintext_1)
            maintext_1 = form_fields[0]
        except:
            maintext_1 = ''
        published = soup.find('abbr', class_="published").text
        print(published, 'publish date')
        main_body = soup.find('div', class_="entry-content")
        img_links = main_body.find_all('img')
        images = [link['src'] for link in img_links]
        maintext = main_body.text
        if maintext == '':
            maintext = theme
        maintext = self.clean_maintext(maintext).strip()
        if maintext == '':
            maintext = theme
        maintext += '\n' + maintext_1.strip()            
        return maintext
        
    def get_data(self, dlink):
        source = requests.get(dlink).text
        soup = BeautifulSoup(source, 'lxml')
        
        published = soup.find('abbr', class_="published").text
        print('published date:', published)
        theme_org = soup.find('h1', class_="ipsType_pagetitle").text
        if "[Правила]" in theme_org:
            return None
        theme = self.remove_phone_in_title(theme_org)
        theme = theme.strip().replace('  ', ' ')
        theme = self.clean_title(theme)
        price = ''
        try:
            text = soup.find_all("div", {"class": "custom-field"})
            maintext_1 = ''
            for item in text:
                maintext_1 += item.text
            form_fields = self.format_fields(maintext_1)
            maintext_1 = form_fields[0]
            if form_fields[1]:
                price = self.get_price(form_fields[1], form_fields[1])
        except:
            maintext_1 = ''
        main_body = soup.find('div', class_="entry-content")
        img_links = main_body.find_all('img')
        images = [link['src'] for link in img_links]
        maintext = main_body.text
        if maintext == '':
            maintext = theme
        maintext = self.clean_maintext(maintext).strip()
        if maintext == '':
            maintext = theme
        maintext += '\n' + maintext_1.strip()
        
        if not price:
            price = self.get_price(maintext, theme_org)
        currency = self.get_currency(maintext, theme_org)
        phones = self.get_phone_num(maintext)
        whats = self.get_whatsapp(maintext)
        if phones == '0-312':
            phones = self.get_phone_num(theme_org)
        
        return {"title": theme[:35], "info": maintext, "price": price, 
                "currency": currency, "phone": phones, "whatsapp": whats, "images": images, 'published': published}
        
    def data(self):
        j = 1
        data = []
        link2 = self.get_links()
        print(len(link2), 'Total number of links')
        while j < min(20, len(link2)):
            source = requests.get(link2[j]).text
            soup = BeautifulSoup(source, 'lxml')
            theme_org = soup.find('h1', class_="ipsType_pagetitle").text
            theme = self.remove_phone_in_title(theme_org)
            theme = theme.strip().replace('  ', ' ')
            try:
                text = soup.find_all("div", {"class": "custom-field"})
                maintext_1 = ''
                for item in text:
                    maintext_1 += item.text
            except:
                maintext_1 = ''
            maintext = soup.find('div', class_="entry-content").text
            if maintext == '':
                maintext = theme
            try:
                maintext = self.clean_maintext(maintext).strip()
            except:
                pass
            if maintext == '':
                maintext = theme
            maintext = maintext.replace('Прикрепленные изображения', '')
            maintext += '\n' + maintext_1.strip()
            price = self.get_price(maintext, theme_org)
            currency = self.get_currency(maintext, theme_org)
            phones = self.get_phone_num(maintext)
            whats = self.get_whatsapp(maintext)
            if phones == '0-312':
                phones = self.get_phone_num(theme_org)
            # whats, phones, theme
            if phones:
                data.append([phones, whats, theme, price, currency])
            j += 1
        return data

    @staticmethod
    def clean_title(text):
        """ Remove: Продаю Срочно ! """
        cleaned_text = re.sub(r'\bпродаю\b', '', text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\bсрочно\b', '', text, flags=re.IGNORECASE)
        cleaned_text = cleaned_text.replace('!', '')
        return cleaned_text.strip()
    
    @staticmethod
    def format_fields(text):
        price = ''
        lines = text.splitlines()
        formatted_lines = []
        formatted_lines.append('<div class="detail-text-points">')
        for i in range(len(lines) - 1):
            if lines[i].strip() and ":" in lines[i]:    # Check if line contains a key
                key = lines[i].strip()                  # Extract the key (before ":")
                value = lines[i + 1].strip()            # Extract the next line as the value
                if "цена" in key.lower():
                    price = value
                formatted_lines.append('<ul class="list-group list-group-horizontal row">')
                formatted_lines.append(f'<li class="list-group-item col-6 col-lg-4">{key}</li> \
                                       <li class="list-group-item col">{value}</li>')
                formatted_lines.append('</ul>')
        formatted_lines.append('</div>')
        fields = "\n".join(formatted_lines)
        return fields, price
    
    @staticmethod
    def get_whatsapp(text):
        search = ['whatsapp', 'Whatsapp', 'Whats app', 'WhatsApp', 'Ватсап', 'вотс ап', 'вотсап', 'Ватс ап',
                  'ватсап', 'Ватцап', 'ватцап', 'Воцап', 'w/a', 'W/A', 'https://wa.me']
        i = 0
        s_index = 0
        while i < len(search):
            try:
                s_index = text.index(search[i])
            except Exception as e:
                pass
            if s_index:
                break
            i += 1
        return 'WA' if s_index > 0 else '-'

    @staticmethod
    def get_new_not(text):
        '''
        Новый в теме
        :param text: string
        :return: True/False
        '''
        search = ['Новый', 'новый', 'НОВЫЙ', 'новую', 'новые']
        i = 0
        s_index = 0
        while i < len(search):
            try:
                s_index = text.index(search[i])
            except Exception as e:
                pass
            if s_index:
                break
            i += 1
        return s_index

    @staticmethod
    def get_currency(text, title):
        '''
        ____ цена/usd ____
        :param text: string
        :return: som/usd
        '''
        search = ['Сом', 'сом', 'СОМ', 'usd', 'Usd', 'USD', 'долл', 'за $', '$']
        currency = ''
        i = 0
        s_index = 0
        while i < len(search):
            try:
                s_index = text.index(search[i])
            except Exception as e:
                pass
            if s_index:
                if i < 3:
                    currency = 'Сом'
                else:
                    currency = 'Долл'
                return currency
            i += 1
        if currency == '':
            i = 0
            s_index = 0
            while i < len(search):
                try:
                    s_index = title.index(search[i])
                except Exception as e:
                    pass
                if s_index:
                    if i < 3:
                        currency = 'Сом'
                    else:
                        currency = 'Долл'
                    return currency
                i += 1
        if currency == '':
            currency = 'Сом'
        return currency

    @staticmethod
    def get_price(text, title):
        '''
        ____ цена/usd ____
        :param text: string
        :return: price_kgs
        '''
        search = ['цена', 'Цена', 'ЦЕНА', 'Цена - $', 'Отдам за']
        search2 = ['Сом', 'сом', 'СОМ', 'usd', 'Usd', 'USD', 'за $', '$', 'USD', 'usd']
        i = 0
        s_index = 0
        while i < len(search):
            try:
                s_index = text.index(search[i])
            except Exception as e:
                pass
            if s_index:
                break
            i += 1
        text_1 = text[s_index + 4:][:10]
        price = ''
        if s_index > 0:
            i = 0
            while i < len(text_1):
                num = text_1[i]
                if num.isnumeric():
                    price += num
                i += 1
        if price == '':
            i = 0
            s_index = 0
            while i < len(search2):
                try:
                    s_index = text.index(search2[i])
                except Exception as e:
                    pass
                if s_index:
                    break
                i += 1
            text_1 = text[:s_index][-8:]
            i = 0
            while i < len(text_1):
                num = text_1[i]
                if num.isnumeric():
                    price += num
                i += 1
        if price == '':
            i = 0
            s_index = 0
            while i < len(search):
                try:
                    s_index = title.index(search[i])
                except Exception as e:
                    pass
                if s_index:
                    break
                i += 1
            text_1 = title[s_index + 3:]
            text_1 = text_1[:10]
            price = ''
            if s_index > 0:
                i = 0
                while i < len(text_1):
                    num = text_1[i]
                    if num.isnumeric():
                        price += num
                    i += 1
            if price == '':
                i = 0
                s_index = 0
                while i < len(search2):
                    try:
                        s_index = title.index(search2[i])
                    except Exception as e:
                        pass
                    if s_index:
                        break
                    i += 1
                text_1 = title[:s_index]
                text_1 = text_1[-7:]
                i = 0
                while i < len(text_1):
                    num = text_1[i]
                    if num.isnumeric():
                        price += num
                    i += 1
        if price == '':
            price = 100
        if re.search(r",\d{1}тыс", text):
            price = price + '00'
        elif re.search(r"[\s]\d{1}тыс", text):
            price = price + '000'
        elif re.search(r"[\s]\d{2}тыс", text):
            price = price + '000'
        return price

    @staticmethod
    def get_phone_num(text):
        phones = re.findall(r"(0\d{9}|0[-\s]??\d{9}|0[-\s]??\d{3}[-\s]??\d{6}|0\(\d{3}\)\d{6}|0\d{3}[-\s]??\d{6}|"
                            r"0\(\d{3}\)[-\s]??\d{3}[-\s]??\d{3}|0\d{3}[-\s]\(\d{3}\)[-\s]\d{6}"
                            r"0\d{3}[-\s]??\d{3}[-\s]??\d{3}|0\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2}|"
                            r"0[-\s]??\d{3}[-\s]??\d{3}[-\s]??\d{3}|0[-\s]??\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2}|"
                            r"\d{12}|996[-\s]??\d{9}|996[-\s]??\d{3}[-\s]??\d{6}|996[-\s]??\d{3}[-\s]??\d{3}[-\s]??\d{3}|"
                            r"996[-\s]??\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2}|996[-\s]??\d{3}[-\s]??\d{3}[-\s]??\d{3}|"
                            r"996[-\s]??\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2}|\(\d{4}\)[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2})",
                            text)
        numbers = []
        numbers2 = []
        for item in phones:
            item2 = ''
            for letter in item:
                if letter.isdigit():
                    item2 += letter
                    item2 = item2[-9:]
            if item2 not in numbers:
                numbers.append(item2)
        for item in numbers:
            digs = '996' + item[0:3] + item[3:]
            numbers2.append(digs)
        phones = numbers2
        if len(phones) == 0:
            phones = re.findall(r"(\d{9}|[-\s]??\d{9}|[-\s]??\d{3}[-\s]??\d{6}|\(\d{3}\)\d{6}|\d{3}[-\s]??\d{6}|"
                                r"\(\d{3}\)[-\s]??\d{3}[-\s]??\d{3}|\d{3}[-\s]\(\d{3}\)[-\s]\d{6}"
                                r"\d{3}[-\s]??\d{3}[-\s]??\d{3}|\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2}|"
                                r"[-\s]??\d{3}[-\s]??\d{3}[-\s]??\d{3}|[-\s]??\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2})",
                                text)
            numbers = []
            numbers2 = []
            for item in phones:
                item2 = ''
                for letter in item:
                    if letter.isdigit():
                        item2 += letter
                        item2 = item2[-9:]
                if item2 not in numbers:
                    numbers.append(item2)
            for item in numbers:
                digs = '996' + item[0:3] + item[3:]
                numbers2.append(digs)
            phones = numbers2
        if len(phones) == 0:
            phones = ''
        return phones

    @staticmethod
    def remove_phone_in_title(theme):
        numbers = re.findall(r"(0\d{9}|0[-\s]??\d{9}|0[-\s]??\d{3}[-\s]??\d{6}|0\(\d{3}\)\d{6}|0\d{3}[-\s]??\d{6}|"
                             r"0\(\d{3}\)[-\s]??\d{3}[-\s]??\d{3}|0\d{3}[-\s]\(\d{3}\)[-\s]\d{6}"
                             r"0\d{3}[-\s]??\d{3}[-\s]??\d{3}|0\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2}|"
                             r"0[-\s]??\d{3}[-\s]??\d{3}[-\s]??\d{3}|0[-\s]??\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2}|"

                             r"\d{9}|[-\s]??\d{9}|[-\s]??\d{3}[-\s]??\d{6}|\(\d{3}\)\d{6}|\d{3}[-\s]??\d{6}|"
                             r"\(\d{3}\)[-\s]??\d{3}[-\s]??\d{3}|\d{3}[-\s]\(\d{3}\)[-\s]\d{6}"
                             r"\d{3}[-\s]??\d{3}[-\s]??\d{3}|\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2}|"
                             r"[-\s]??\d{3}[-\s]??\d{3}[-\s]??\d{3}|[-\s]??\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2}|"

                             r"\d{12}|996[-\s]??\d{9}|996[-\s]??\d{3}[-\s]??\d{6}|996[-\s]??\d{3}[-\s]??\d{3}[-\s]??\d{3}|"
                             r"996[-\s]??\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2}|996[-\s]??\d{3}[-\s]??\d{3}[-\s]??\d{3}|"
                             r"996[-\s]??\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2}|\(\d{4}\)[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2})",
                             theme)
        if len(numbers) == 0:
            numbers = re.findall(r"(\d{9}|[-\s]??\d{9}|[-\s]??\d{3}[-\s]??\d{6}|\(\d{3}\)\d{6}|\d{3}[-\s]??\d{6}|"
                                 r"\(\d{3}\)[-\s]??\d{3}[-\s]??\d{3}|\d{3}[-\s]\(\d{3}\)[-\s]\d{6}"
                                 r"\d{3}[-\s]??\d{3}[-\s]??\d{3}|\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2}|"
                                 r"[-\s]??\d{3}[-\s]??\d{3}[-\s]??\d{3}|[-\s]??\d{3}[-\s]??\d{2}[-\s]??\d{2}[-\s]??\d{2})",
                                 theme)
        if len(numbers) > 0:
            for number in numbers:
                theme = theme.replace(number, '')
        return theme

    @staticmethod
    def clean_maintext(text):
        search = 'Прикрепленные изображения'
        s_index = text.find(search)
        if s_index != -1:
            text = text[:s_index]   
        
        lines = text.splitlines()  # Split into list of lines
        cleaned_lines = [line.strip() for line in lines if line.strip() and "Сообщение отредактировал" not in line]  # Remove empty lines
        text = "\n".join(cleaned_lines) 
        return text

if __name__ == "__main__":
    # forums: 459 -1kv, 460 -2kv 461 -3kv 461-prock kv
    # 225 doma, 226 - comm pomeshenia, 232 - prochee nedvijka
    # 283 - cars, 284 - tech auto, 
    topics= {"283": "Авто",
            "459": "Недвижимость Квартира",
            "460": "Недвижимость Квартира",
            "225": "Недвижимость Дом"}
    cl = Client('uralbi@naver.com', 'letsdo$79', '283', 2)
    cl.run()
    
