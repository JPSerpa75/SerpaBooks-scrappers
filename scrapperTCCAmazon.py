from datetime import datetime
import dateparser
import mysql.connector

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


def handleAutor(autor):
        
    sql = "SELECT * FROM autor a WHERE a.nm_autor like  %s"  
    val = ("%" + autor + "%",)
    cursor.execute(sql, val)
    resultado = cursor.fetchall()

    if(resultado):
        return resultado[0][0]
    

    sql = "INSERT INTO autor (nm_autor) VALUES (%s)"
    val = (autor,)
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

    sql = "INSERT INTO info_livro (titulo_livro, nota_livro, resumo_livro, sinopse_livro, idioma_livro, id_autor )" 
    sql = sql +  " VALUES (%s, %s, %s, %s, %s, %s)"
    val = (livro['Título'], livro['Nota'], livro['Resumo'], livro['Sinopse'], livro['Idioma'], livro['Autor'], )
    cursor.execute(sql, val)
    db.commit()
    idInfoLivro = cursor.lastrowid

    sql = "INSERT INTO livro (url_imagem_livro, numero_paginas_livro, dt_publicacao_livro, isbn_10_livro, isbn_13_livro, dt_cadastro_livro, id_editora, id_capa, id_info_livro)" 
    sql = sql +  " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    val = ( livro['URL da Imagem'], livro['Numero de páginas'], livro['Data publicação'],  livro['Isbn 10'], livro['Isbn 13'], livro['Data cadastro'], livro['Editora'], livro['Capa'], idInfoLivro, )
    cursor.execute(sql, val)
    db.commit()

    return cursor.lastrowid


def handlePrecoAmazon(preco_info):

    sql = "SELECT * FROM preco_amazon pa WHERE pa.id_livro = %s AND pa.id_capa = %s"  
    val = (preco_info['Livro'], preco_info['Capa'])
    cursor.execute(sql, val)
    resultado = cursor.fetchall()

    if(resultado):
        idPrecoAmazon = resultado[0][0]
        sql = "UPDATE preco_amazon SET preco_amazon = %s, link_amazon = %s, img_amazon = %s, dt_cadastro_preco_amazon = %s WHERE id_preco_amazon = %s"
        val = (preco_info['Preço'], preco_info['Link'],  preco_info['URL da Imagem'], preco_info['Data cadastro'], idPrecoAmazon)
        cursor.execute(sql, val)
        db.commit()
        return "ok"
    

    sql = "INSERT INTO preco_amazon (link_amazon, img_amazon, preco_amazon, dt_cadastro_preco_amazon, id_livro, id_capa ) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (preco_info['Link'], preco_info['URL da Imagem'], preco_info['Preço'], preco_info['Data cadastro'], preco_info['Livro'], preco_info['Capa'],)
    cursor.execute(sql, val)
    db.commit()

    return "ok";

def scrapper( ):

    import time
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    import re
    from bs4 import BeautifulSoup


    # Configurações do navegador
    options = Options()
    #options.add_argument("--headless")  # Executar o Chrome em modo headless (sem interface gráfica)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36")
    service = Service("D:\Downloads\chromedriver-win64\chromedriver.exe")  # Caminho para o executável do ChromeDriver
    driver = webdriver.Chrome(service=service, options=options)

    url = "https://www.amazon.com.br/gp/bestsellers/books/ref=sv_b_1"
    driver.get(url)

    # Aguardar um pouco para que a página seja completamente carregada
    time.sleep(5)

    # Definir a quantidade de vezes que você deseja descer a página
    num_scrolls = 20

    for i in range(num_scrolls):
        # Definir o deslocamento vertical (200 pixels aqui) para fazer o scroll
        driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(1)  # Tempo de espera entre cada deslocamento

    # Aguardar um tempo para que o conteúdo adicional seja carregado, se necessário
    time.sleep(7)


    # Obter o conteúdo da página
    data = driver.page_source

    soup = BeautifulSoup(data, 'html.parser')

    cards = soup.find_all('div', class_=["p13n-sc-uncoverable-faceout"] )

    livros = []

    for card in cards:
        link = card.find('a', class_=["a-link-normal"])
        img = card.find('img', class_=["a-dynamic-image p13n-sc-dynamic-image p13n-product-image"])
        autor = card.find('a', class_=["a-size-small a-link-child"])
        nota = card.find('span', class_=["a-icon-alt"])
        capa = card.find('span', class_=["a-size-small a-color-secondary a-text-normal"])
        preco = card.find('span', class_=["_cDEzb_p13n-sc-price_3mJ9Z"])
        autor2 = card.find('span', class_=["a-size-small a-color-base"])  

        if link is not None and img is not None and capa is not None:
            autor_text = ""
            nota_text = None
            preco_text = "0.0"

            if autor is not None:
                autor_text = autor.find('div', class_=["_cDEzb_p13n-sc-css-line-clamp-1_1Fn1y"]).text.strip()
            else:
                autor_text = autor2.find('div', class_=["_cDEzb_p13n-sc-css-line-clamp-1_1Fn1y"]).text.strip()  

            if nota is not None:
                nota_text = (nota.text.strip()).split(" ")[0]
                nota_text = nota_text.replace(',', '.')

            if preco is not None:
                preco_match = re.search(r"R\$\s*(\d+,\d+)", preco.text.strip())
                preco_text = preco_match.group(1) if preco_match else "Preço não disponível"
                preco_text = preco_text.replace(',', '.')


            link_text = "https://www.amazon.com.br" + link['href']
            title_text = img['alt']
            img_src = img['src']
            capa_text = capa.text.strip()
            
            livro_info = {
                'Link': link_text,
                'Título': title_text,
                'URL da Imagem': img_src,
                'Autor': autor_text,
                'Nota': nota_text,
                'Capa': capa_text,
                'Preço': preco_text
            }

            livros.append(livro_info)   



    print(len(livros))
    for livro in livros:
        print(livro['Título'])


    for livro in livros:

        idCapa = handleCapa(livro['Capa'])
        idAutor = handleAutor(livro['Autor'])

        sql = "SELECT * FROM info_livro il WHERE il.titulo_livro LIKE %s"
        val = ("%" + livro['Título'] + "%",)
        cursor.execute(sql, val)
        resultadoInfoLivro = cursor.fetchall()

        if(resultadoInfoLivro):
            sql = "SELECT * FROM livro l WHERE l.id_info_livro = %s and l.id_capa = %s"
            val = (resultadoInfoLivro[0][0], idCapa)
            cursor.execute(sql, val)
            resultadoLivro = cursor.fetchall()

            print("Livro já existe no banco")           

            if(resultadoLivro):
                amazon_info = {
                    'Link': livro['Link'],
                    'URL da Imagem': livro['URL da Imagem'],
                    'Preço': livro['Preço'],
                    'Livro': resultadoLivro[0][0],
                    'Capa': idCapa,
                    'Data cadastro': datetime.now()
                }

                handlePrecoAmazon(amazon_info)


        else:
            url = livro['Link']
            driver.get(url)
            print(url)
            time.sleep(5)
            data = driver.page_source

            soup = BeautifulSoup(data, 'html.parser')
            cards = soup.find_all('div', class_=["centerColumn"] )


            for card in cards:
                info = card.find('div', class_=["a-expander-content a-expander-partial-collapse-content"])

                # if info.find_all('p') is None:
                #     info = card.find('div', class_=["a-expander-collapsed-height a-row a-expander-container a-spacing-base a-expander-partial-collapse-container"])
                descricao = info.find_all('p')
                resumo = info.find('p')
                lista = card.find('ol', class_=["a-carousel"])
                numeroPag = lista.find('div', id=["rpi-attribute-book_details-fiona_pages"])
                idioma =  lista.find('div', id=["rpi-attribute-language"])
                editora = lista.find('div', id=["rpi-attribute-book_details-publisher"])
                dataPublicacao = lista.find('div', id=["rpi-attribute-book_details-publication_date"])
                isbn10 = lista.find('div', id=["rpi-attribute-book_details-isbn10"])
                isbn13 = lista.find('div', id=["rpi-attribute-book_details-isbn13"])

 
                if dataPublicacao is not None and isbn10 is not None:
                    resumo_text = None
                    sinopse_text = None

                    if descricao and resumo:
                        resumo_text = resumo.text.strip()
                        if len(resumo_text) > 500:
                            sinopse_text = resumo_text
                            resumo_text = None
                        else:
                            sinopse_text = " ".join([p.text.strip() for p in descricao[1:]])
                    else:
                        sinopse_text = info.find('span').text.strip()
    

                    numeroPag_text = numeroPag.find('div', class_=["a-section a-spacing-none a-text-center rpi-attribute-value"]).text.strip().split(" ")[0]
                    
                    idioma_text = None
                    if idioma is not None:
                        idioma_text = idioma.find('div', class_=["a-section a-spacing-none a-text-center rpi-attribute-value"]).text.strip()
                    
                    editora_text = editora.find('div', class_=["a-section a-spacing-none a-text-center rpi-attribute-value"]).text.strip()
                    dataPublicacao_text = converter_para_date(dataPublicacao.find('div', class_=["a-section a-spacing-none a-text-center rpi-attribute-value"]).text.strip())
                    isbn10_text = isbn10.find('div', class_=["a-section a-spacing-none a-text-center rpi-attribute-value"]).text.strip()
                    isbn13_text = isbn13.find('div', class_=["a-section a-spacing-none a-text-center rpi-attribute-value"]).text.strip()
                    dataCadastro = datetime.now()

                    idEditora = handleEditora(editora_text)

                    livro_info = {
                        'Título': livro['Título'],
                        'URL da Imagem': livro['URL da Imagem'],
                        'Nota': livro['Nota'],
                        'Resumo': resumo_text,
                        'Sinopse': sinopse_text,
                        'Numero de páginas': int(numeroPag_text),
                        'Idioma': idioma_text,
                        'Data publicação': dataPublicacao_text,
                        'Isbn 10': isbn10_text,
                        'Isbn 13': isbn13_text,
                        'Data cadastro': dataCadastro,
                        'Editora': idEditora,
                        'Autor': idAutor,
                        'Capa': idCapa
                    }

                    idLivro = handleLivro(livro_info)
                    
                    amazon_info = {
                        'Link': livro['Link'],
                        'URL da Imagem': livro['URL da Imagem'],
                        'Preço': livro['Preço'],
                        'Titulo': livro['Título'],
                        'Livro': idLivro, 
                        'Capa': idCapa,
                        'Data cadastro': dataCadastro
                    }

                    print(handlePrecoAmazon(amazon_info))
            

    # Fechar o navegador
    driver.quit()

scrapper()