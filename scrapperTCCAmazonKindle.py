from datetime import datetime
import mysql.connector
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import dateparser
import re

from bs4 import BeautifulSoup    

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="serpabooksdb"
)       

cursor = db.cursor()


def converter_para_date(data_str):
    data_datetime = dateparser.parse(data_str, languages=['pt']).date()
    return data_datetime;

def limparBd():
    db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="serpabooksdb"
    )       

    cursor = db.cursor() 

    sql = "select l.id_livro, il.id_info_livro, il.titulo_livro, l.id_capa, pm.id_preco_magalu, pm.link_magalu, pml.id_preco_mercado_livre, pml.link_mercado_livre " 
    sql = sql + "from livro l "
    sql = sql + "inner join info_livro il on il.id_info_livro = l.id_info_livro "
    sql = sql + "inner join capa c on c.id_capa = l.id_capa "
    sql = sql + "left join preco_magalu pm on pm.id_livro = l.id_livro "
    sql = sql + "left join preco_mercado_livre pml on pml.id_livro = l.id_livro "
    sql = sql + "where pm.id_preco_magalu is null and pml.id_preco_mercado_livre is null and c.ds_capa != 'eBook Kindle';"
    #print(sql)

    cursor.execute(sql)
    resultado = cursor.fetchall()

    for registro in resultado:
        sql = "delete from preco_amazon where id_livro = %s"
        val = (registro[0],)
        cursor.execute(sql, val)
        
        sql = "delete from livro where id_livro = %s"
        val = (registro[0],)
        cursor.execute(sql, val)
        
        sql = "delete from info_livro where id_info_livro = %s"
        val = (registro[1],)
        cursor.execute(sql, val)

        db.commit()

        
def handleCapa(capa):
    
    sql = "SELECT * FROM capa c WHERE c.ds_capa like  %s"  
    val = ("%" + capa + "%",)
    cursor.execute(sql, val)
    resultado = cursor.fetchall()

    if(resultado):
        return resultado[0][0]
    

    sql = "INSERT INTO capa (ds_capa) VALUES (%s)"
    val = (capa,)
    cursor.execute(sql, val)
    db.commit()

    return cursor.lastrowid;

def handleEditora(editora):

    sql = "SELECT * FROM editora e WHERE e.nm_editora like  %s"  
    val = ("%" + editora + "%",)
    cursor.execute(sql, val)
    resultado = cursor.fetchall()

    if(resultado):
        return resultado[0][0]
    

    sql = "INSERT INTO editora (nm_editora) VALUES (%s)"
    val = (editora,)
    cursor.execute(sql, val)
    db.commit()

    return cursor.lastrowid;

def handleLivro(livro):

    sql = "SELECT * FROM livro l WHERE l.id_info_livro = %s and l.id_capa = %s"
    val = (livro['idInfoLivro'], livro['idCapa'])
    cursor.execute(sql, val)
    resultadoLivro = cursor.fetchall()    

    if resultadoLivro:
        return resultadoLivro[0][0]

    if(livro['idEditora'] != ''):
        sql = "INSERT INTO livro (url_imagem_livro, numero_paginas_livro, dt_publicacao_livro, dt_cadastro_livro, id_editora, id_capa, id_info_livro)" 
        sql = sql +  " VALUES (%s, %s, %s, %s, %s, %s, %s)"
        val = ( livro['urlImagemLivro'], livro['numeroPaginas'], livro['dataPublicacao'],  livro['dataCadastro'], livro['idEditora'], livro['idCapa'], livro['idInfoLivro'], )
        cursor.execute(sql, val)
        db.commit()
        return cursor.lastrowid

    sql = "INSERT INTO livro (url_imagem_livro, numero_paginas_livro, dt_publicacao_livro, dt_cadastro_livro, id_capa, id_info_livro)" 
    sql = sql +  " VALUES (%s, %s, %s, %s, %s, %s)"
    val = ( livro['urlImagemLivro'], livro['numeroPaginas'], livro['dataPublicacao'],  livro['dataCadastro'], livro['idCapa'], livro['idInfoLivro'], )
    cursor.execute(sql, val)
    db.commit()
    return cursor.lastrowid


def handlePrecoAmazon(preco_info):

    sql = "SELECT * FROM preco_amazon pa WHERE pa.id_livro = %s AND pa.id_capa = %s"  
    val = (preco_info['idLivro'], preco_info['idCapa'])
    cursor.execute(sql, val)
    resultado = cursor.fetchall()

    if(resultado):
        idPrecoAmazon = resultado[0][0]
        sql = "UPDATE preco_amazon SET preco_amazon = %s, link_amazon = %s, img_amazon = %s, dt_cadastro_preco_amazon = %s WHERE id_preco_amazon = %s"
        val = (preco_info['preco'], preco_info['link'],  preco_info['urlImagem'], preco_info['dataCadastro'], idPrecoAmazon)
        cursor.execute(sql, val)
        db.commit()
        return "ok"
    

    sql = "INSERT INTO preco_amazon (link_amazon, img_amazon, preco_amazon, dt_cadastro_preco_amazon, id_livro, id_capa ) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (preco_info['link'], preco_info['urlImagem'], preco_info['preco'], preco_info['dataCadastro'], preco_info['idLivro'], preco_info['idCapa'],)
    cursor.execute(sql, val)
    db.commit()

    return "ok";

def processarLivro(driver, livro, linkKindleText):
    data = driver.page_source

    soup = BeautifulSoup(data, 'html.parser')
    cards = soup.find_all('div', class_=["centerColumn"] )
    righColumn = soup.find('div', id=['rightCol'])
    leftColumn = soup.find('div', id=['leftCol'])


    for card in cards:
        lista = card.find('ol', class_=["a-carousel"])
        numeroPag = lista.find('div', id=["rpi-attribute-book_details-ebook_pages"])

        editora = lista.find('div', id=["rpi-attribute-book_details-publisher"])
        dataPublicacao = lista.find('div', id=["rpi-attribute-book_details-publication_date"])

        preco_text = "0.0"
        if righColumn and leftColumn:
            preco = righColumn.find('span', class_=['a-size-medium a-color-price'])
            img = leftColumn.find('img', class_=['a-dynamic-image a-stretch-horizontal'])

            if img is None:
                img = leftColumn.find('img', class_=['a-dynamic-image a-stretch-vertical'])
            

            if preco is not None:
                preco_match = re.search(r"R\$\s*(\d+,\d+)", preco.text.strip())
                preco_text = preco_match.group(1) if preco_match else "Preço não disponível"
                preco_text = preco_text.replace(',', '.')


        capa_text = 'eBook Kindle'

        idEditora = ''
        if editora is not None:
            editora_text = editora.find('div', class_=["a-section a-spacing-none a-text-center rpi-attribute-value"]).text.strip()
            idEditora = handleEditora(editora_text)
            
        numeroPag_text = numeroPag.find('div', class_=["a-section a-spacing-none a-text-center rpi-attribute-value"]).text.strip().split(" ")[0]            
        dataPublicacao_text = converter_para_date(dataPublicacao.find('div', class_=["a-section a-spacing-none a-text-center rpi-attribute-value"]).text.strip())
        dataCadastro = datetime.now()



        idCapa = handleCapa(capa_text);


        livro_kindle = {
            'urlImagemLivro': img['src'],
            'numeroPaginas': int(numeroPag_text),
            'dataPublicacao': dataPublicacao_text,
            'dataCadastro': dataCadastro,
            'idEditora': idEditora,
            'idCapa': idCapa,
            'idInfoLivro': livro['idInfoLivro']
        }

        idLivro = handleLivro(livro_kindle)
                    
        amazon_info = {
            'link': linkKindleText,
            'urlImagem': img['src'],
            'preco': preco_text,
            'Titulo': livro['titulo'],
            'idLivro': idLivro, 
            'idCapa': idCapa,
            'dataCadastro': dataCadastro
        }

        print(handlePrecoAmazon(amazon_info))



    
            
def rasparLivros(livros):

    # Configurações do navegador
    options = Options()
    #options.add_argument("--headless")  # Executar o Chrome em modo headless (sem interface gráfica)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36")
    service = Service("D:\Downloads\chromedriver-win64\chromedriver.exe")  # Caminho para o executável do ChromeDriver
    driver = webdriver.Chrome(service=service, options=options)

    for livro in livros:
        url = livro["linkAmazon"]
        driver.get(url)

        print("Link Livro : " + livro["linkAmazon"])
        print("Titulo Livro : " + livro["titulo"])

        time.sleep(8)
        
        try:
            kindle = driver.find_element(By.ID, "tmm-grid-swatch-KINDLE")
     
            data = driver.page_source
            soup = BeautifulSoup(data, 'html.parser')
            card = soup.find('div', id=["tmm-grid-swatch-KINDLE"] )

            linkKindle = card.find("a", class_="a-button-text a-text-left")
            linkKindleText = "https://www.amazon.com.br" + linkKindle["href"]
            print(linkKindleText)

            kindle = kindle.find_element(By.TAG_NAME, "a")
            kindle.send_keys(Keys.RETURN)
            time.sleep(4)
            processarLivro(driver, livro, linkKindleText)
            print("Versão Kindle Cadastrada!")
        except Exception:
            print("Esse livro não possui uma versão kindle")
        
    driver.quit()
           
def scrapperLivros():
    db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="serpabooksdb"
    )       

    cursor = db.cursor()

   
    sql = "select l.id_livro, l.isbn_10_livro, l.isbn_13_livro, il.id_info_livro, il.titulo_livro, c.id_capa, c.ds_capa, pa.id_preco_amazon, pa.link_amazon "
    sql = sql + "from livro l "
    sql = sql + "inner join info_livro il on il.id_info_livro = l.id_info_livro "
    sql = sql + "inner join capa c on c.id_capa = l.id_capa "
    sql = sql + "inner join autor a on a.id_autor = il.id_autor "
    sql = sql + "inner join preco_amazon pa on pa.id_livro = l.id_livro "
    sql = sql + "where c.ds_capa != 'eBook Kindle' "
    sql = sql + "order by l.id_livro desc limit 50; "

    print(sql)
    cursor.execute(sql)
    resultado = cursor.fetchall()

    livros = []
    for registro in resultado:
        livro_info = {
        'id': registro[0],
        'isbn10': registro[1],
        'isbn13': registro[2],
        'idInfoLivro': registro[3],
        'titulo': registro[4],
        'idCapa': registro[5],
        'capa': registro[6],        
        'idPrecoAmazon': registro[7],
        'linkAmazon': registro[8],
        }

        livros.append(livro_info)

    rasparLivros(livros)

limparBd()
scrapperLivros()

# def atualizarPrecoAmazon(driver, livro):

#     data = driver.page_source

#     soup = BeautifulSoup(data, 'html.parser')
#     righColumn = soup.find('div', id=['rightCol'])
#     leftColumn = soup.find('div', id=['leftCol'])

#     if righColumn is not None and leftColumn is not None:
#         preco_text = "0.0"
       
#         preco = righColumn.find('span', class_=['a-size-medium a-color-price'])
#         img = leftColumn.find('img', class_=['a-dynamic-image a-stretch-horizontal'])
            
#         if img is None:
#             img = leftColumn.find('img', class_=['a-dynamic-image a-stretch-vertical'])

#         if preco is not None:
#             preco_match = re.search(r"R\$\s*(\d+,\d+)", preco.text.strip())
#             preco_text = preco_match.group(1) if preco_match else "Preço não disponível"
#             preco_text = preco_text.replace(',', '.')

#         capa_text = 'eBook Kindle'
#         dataCadastro = datetime.now()
#         idCapa = handleCapa(capa_text);

#         amazon_info = {
#         'link': livro['linkAmazon'],
#         'urlImagem': img['src'],
#         'preco': preco_text,
#         'Titulo': livro['titulo'],
#         'idLivro': livro['id'], 
#         'idCapa': idCapa,
#         'dataCadastro': dataCadastro
#         }

#         handlePrecoAmazon(amazon_info)      

# def rasparLivrosKindle(livros):
#      # Configurações do navegador
#     options = Options()
#     #options.add_argument("--headless")  # Executar o Chrome em modo headless (sem interface gráfica)
#     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36")
#     service = Service("D:\Downloads\chromedriver-win64\chromedriver.exe")  # Caminho para o executável do ChromeDriver
#     driver = webdriver.Chrome(service=service, options=options)

#     for livro in livros:
#         url = livro["linkAmazon"]
#         driver.get(url)

#         print("Link Livro : " + livro["linkAmazon"])
#         print("Titulo Livro : " + livro["titulo"])

#         # Aguardar um pouco para que a página seja completamente carregada
#         time.sleep(3)
#         atualizarPrecoAmazon(driver, livro)
#         print("Versão Kindle atualizada com sucesso!")
        
#     driver.quit()


# def scrapperOnlyKindle():
#     db = mysql.connector.connect(
#         host="localhost",
#         user="root",
#         password="root",
#         database="serpabooksdb"
#     )       

#     cursor = db.cursor()
   
#     sql = "select l.id_livro, l.isbn_10_livro, l.isbn_13_livro, il.id_info_livro, il.titulo_livro, c.id_capa, c.ds_capa, pa.id_preco_amazon, pa.link_amazon "
#     sql = sql + "from livro l "
#     sql = sql + "inner join info_livro il on il.id_info_livro = l.id_info_livro "
#     sql = sql + "inner join capa c on c.id_capa = l.id_capa "
#     sql = sql + "inner join autor a on a.id_autor = il.id_autor "
#     sql = sql + "inner join preco_amazon pa on pa.id_livro = l.id_livro "
#     sql = sql + "where c.ds_capa == 'eBook Kindle'; "
#     #print(sql)
#     cursor.execute(sql)
#     resultado = cursor.fetchall()

#     livros = []
#     for registro in resultado:
#         livro_info = {
#         'id': registro[0],
#         'isbn10': registro[1],
#         'isbn13': registro[2],
#         'idInfoLivro': registro[3],
#         'titulo': registro[4],
#         'idCapa': registro[5],
#         'capa': registro[6],        
#         'idPrecoAmazon': registro[7],
#         'linkAmazon': registro[8],
#         }

#         livros.append(livro_info)

#     rasparLivrosKindle(livros)


#scrapperOnlyKindle()

