from urllib import request
from bs4 import BeautifulSoup as bs
from json import dumps


markets_info = {}
root = 'http://mysupermarket.org.ua/'
parser = 'html.parser'


def init():
    main = request.urlopen(root)
    soup = bs(main, parser)
    
    markets_list = soup.find(class_='shop', style="color:#F00")
    markets = markets_list.find_all('a')[:-1]
    
    for market in markets:
        markets_info[market.find('b').text] = {'href': root + market.get('href')}

        print('parse ' + market.find('b').text, end='')
        print('.....link is ' + root + market.get('href'))

        markets_info[market.find('b').text]['categories'] = parse_category(root + market.get('href'))


def parse_category(href):
    market = request.urlopen(href)
    soup = bs(market, parser)
    _categories = soup.find_all("p", style="color:#F00")[1].find_all('a', attrs={'class': None})

    categories = {}
    for category in _categories:
        categories[category.text] = {'href': root + category.get('href')}
        print('\tparse ' + category.text, end='')
        print('.....link is ' + root + category.get('href'))
        categories[category.text]['sections'] = parse_names(root + category.get('href'))

    return categories


def parse_names(href):
    my_category = request.urlopen(href)
    category_soup = bs(my_category, parser)
    search = category_soup.find_all("p", style="color:#F00")

    categories = ''

    for i in search:
        if 'НАЗВАНИЯ' in i.findChildren()[0].text:
            categories = i.findChildren('a', attrs={'class': None})

    sections = {}

    for link in categories:
        sections[link.text] = {'href': root + link.get('href')}
        print('\t\tparse ' + link.text, end='')
        print('.....link is ' + root + link.get('href'))
        sections[link.text]['manufacturers'] = parse_manufacturer(root + link.get('href'))

    return sections


def parse_manufacturer(href):
    manufacturer = request.urlopen(href)
    soup = bs(manufacturer, parser)
    search = soup.find_all("p", style="color:#F00")
    categories = ''

    for i in search:
        if 'ТОРГОВЫЕ МАРКИ' in i.findChildren()[0].text:
            categories = i

    manufacturers = {}
    manufacturers[categories.find('a').text] = {'href': root + categories.find('a').get('href')}

    print('\t\t\tparse ' + categories.find('a').text, end='')
    print('.....link is ' + root + categories.find('a').get('href'))

    for i in categories.find('a').find_next_siblings('a'):
        manufacturers[i.text] = {'href': root + i.get('href')}
        print('\t\t\tparse ' + i.text, end='')
        print('.....link is ' + root + i.get('href'))
        manufacturers[i.text]['goods'] = parse_goods(root + i.get('href'))

    return manufacturers


def parse_goods(href):
    goods = request.urlopen(href)
    soup = bs(goods, parser)
    result = {}
    for i in soup.find_all('td', class_='tov'):
        if i.findChildren('a', class_='price'):
            link = i.find('a').get('href').replace('\n', '')
            name = i.find('p').text.strip()
            count = i.findNextSibling().find('p').text
            print('\t\t\t\tparse ' + name, ' %s (g\kg\pcs)' % count, end='')
            print('.....link is ' + root + link)

            sub_result = parse_good(root + link)

            result[name] = {'href': root + link,
                            'count': count,
                            'prices': sub_result['prices'],
                            'image': sub_result['image']
                            }

    return result


def parse_good(href):
    good = request.urlopen(href)
    soup = bs(good, parser)

    image = root + soup.find('div', id='images').find('img').get('src')
    print('\t\t\t\t\t image by the link...%s' % image)

    filtered_goods = []
    for price in soup.find_all('p', class_='date'):
        if len(price.findChildren()) != 0:
            break
        filtered_goods.append(price)

    filtered_goods = filtered_goods[:-1]

    prices = {}

    for good in filtered_goods:
        date = good.text
        price = good.find_previous('b').text.strip(' grn')
        try:
            market = good.find_previous('b').next_sibling.strip('- ')
            prices[market] = (price, date)
            print("\t\t\t\t\t price is: %s; last_updated at: %s; market: %s;" % (price, date, market))
        except AttributeError:
            pass

    print('\t\t\t\t\t done')
    return {'prices': prices, 'image': image}

init()

with open('result1.json', 'w+') as json_file:
    init()
    json_file.write(dumps(markets_info))

