import warnings
warnings.filterwarnings("ignore")

import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

import pandas as pd

import os
import re

def crawl_drugbank(entities, savepath="../data/entities/map/compounds/DrugBank.tsv"):
    os.makedirs(os.path.dirname(savepath), exist_ok=True)
    if os.path.isfile(savepath):
        drbk =  pd.read_csv(savepath, sep="\t")
    else:
        drbk = entities[entities["entity"].str.contains("Compound::DB")]
        drbk["entity_id"] = drbk["entity"].str.split("::", expand=True)[1]

        print(len(drbk))
        drbk = drbk[["entity", "entity_id"]]
        drbk["name"] = None
        drbk["InChIKey"] = None
        drbk["type"] = None
        drbk["phase"] = None
        drbk["weight"] = None
        drbk["chemical_formula"] = None
        drbk.reset_index(drop=True, inplace=True)
    
    print("Total: {}".format(len(drbk)))   
    processed = len(drbk[~drbk.name.isna()])
    print("Processed: {}".format(processed))
    print("Need to process: {}".format(len(drbk) - processed))
    
    for i, id in enumerate(drbk.entity_id.tolist()[processed:]):
        count = processed + i
        print("{}. {}".format(count + 1, id))
        doc = requests.get(f"https://go.drugbank.com/drugs/{id}", allow_redirects=True).content
        soup = BeautifulSoup(doc)

        contents = soup.find_all("dl")[0]
        keys = [x.get("id") for x in contents.find_all("dt")]
        values = [x.get_text() for x in contents.find_all("dd")]
        drug_dict = dict(zip(keys, values))
        drbk.loc[count, "name"] = drug_dict.get("generic-name", drug_dict.get("name"))
        drbk.loc[count, "type"] = drug_dict.get("type")
        drbk.loc[count, "phase"] = drug_dict.get("groups")
        drbk.loc[count, "weight"] = drug_dict.get("weight")
        drbk.loc[count, "chemical_formula"] = drug_dict.get("chemical-formula")
        
        # Get InChI Key
        contents = soup.find_all("dl")
        for tb in contents:
            keys = tb.find_all("dt")
            values = tb.find_all("dd")
            for j in range(len(keys)):
                if keys[j].get_text() == "InChI Key":
                    drbk.loc[count, "InChIKey"] = values[j].get_text()
                    break
        
        drbk.to_csv(savepath, sep="\t", index=False)
        
    return drbk
        
        
def crawl_zinc(entities, savepath="../data/drkg/map/compounds/ZINC.tsv"):
    os.makedirs(os.path.dirname(savepath), exist_ok=True)
    if os.path.isfile(savepath):
        df = pd.read_csv(savepath, sep="\t")
    else:
        df = entities[entities.entity.str.contains("Compound::zinc")]
        df["entity_id"] = df["entity"].str.split("::", expand=True)[1].str.split(
            ":", expand=True
        )[1]
        print("Number of compounds: {}".format(len(df)))
        df = df[["entity", "entity_id"]].reset_index(drop=True)
        df["InChIKey"] = None
        df["chemical_formula"] = None

    print("Total: {}".format(len(df)))
    processed = len(df[~df.InChIKey.isna()])
    print("Processed: {}".format(processed))
    print("Need to process: {}".format(len(df) - processed))

    for i, id in enumerate(df.entity_id.tolist()[processed:]):
        count = processed + i
        print("{}. {}".format(count + 1, id))
        doc = requests.get(f"https://zinc15.docking.org/substances/{id}", allow_redirects=True).content
        soup = BeautifulSoup(doc)
        
        df.loc[count, "InChIKey"] = soup.find(id="substance-inchikey-field").get("value")
        for tb in soup.find_all("table"):
            headers = tb.find_all("th")
            values = tb.find_all("td")
            
            for j in range(len(headers)):
                if headers[j].get_text() == "Mol Formula":
                    mol_formula = values[j].get_text()
                    break
                
        df.loc[count, "chemical_formula"] = mol_formula
        
        df.to_csv(savepath, sep="\t", index=False)
        
    return df


def crawl_chebi(entities, savepath):
    
    os.makedirs(os.path.dirname(savepath), exist_ok=True)
    
    if os.path.isfile(savepath):
        df = pd.read_csv(savepath, sep="\t")
    else:
        df = entities[entities.entity.str.contains(
            "Compound::CHEBI:") | compounds.entity.str.contains("Compound::chebi:")]
        df["entity_id"] = df["entity"].str.split("::", expand=True)[1].str.upper()
        print("Number of compounds: {}".format(len(df)))
        df = df[["entity", "entity_id"]].reset_index(drop=True)
        df["name"] = None
        df["InChIKey"] = None

    print("Total: {}".format(len(df)))
    processed = len(df[~df.name.isna()])
    print("Processed: {}".format(processed))
    print("Need to process: {}".format(len(df) - processed))

    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')

    for i, id in enumerate(df.entity_id.tolist()[processed:]):
        count = processed + i
        print("{}. {}".format(count + 1, id))
        url = f"https://www.ebi.ac.uk/chebi/searchId.do?chebiId={id}"
        doc = requests.get(url, allow_redirects=True).content
        soup = BeautifulSoup(doc)
        contents = soup.find_all("table")[1].find_all("table")[0].find_all("table")[0].find_all("table")[0]

        for row in contents.find_all("tr"):
            k = row.find_all("td")[0].get_text().strip(" \n")
            if k == "ChEBI Name":
                df.loc[count, "name"] = row.find_all("td")[1].get_text().strip(" \n")
            if k == "Secondary ChEBI IDs":
                synonyms = row.find_all("td")[1].get_text().strip(" \n").split(", ")
        
        contents = soup.find_all("table", class_="chebiTableContent")
        for tb in contents:
            row = tb.find_all("td")
            if row[0].get_text() == "InChIKey":
                df.loc[count, "InChIKey"] = row[1].get_text()
                break
        
        df.to_csv(savepath, sep="\t", index=False)
        
    return df


def crawl_molport(entities, savepath):
    os.makedirs(os.path.dirname(savepath), exist_ok=True)
    
    if os.path.isfile(savepath):
        df = pd.read_csv(savepath, sep="\t")
    else:
        molport = entities[entities.entity.str.contains("Compound::molport")]
        df = molport.copy()
        df["entity_id"] = df["entity"].str.split("::", expand=True)[1].str.split(
            ":", expand=True)[1]
        df
        print("Number of compounds: {}".format(len(df)))
        df = df[["entity", "entity_id"]].reset_index(drop=True)
        df["name"] = None
        df["weight"] = None
        df["chemical_formula"] = None
        df["InChIKey"] = None
        
    print("Total: {}".format(len(df)))
    processed = len(df[~df.name.isna()])
    print("Processed: {}".format(processed))
    print("Need to process: {}".format(len(df) - processed))

    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')

    for i, id in enumerate(df.entity_id.tolist()[processed:]):
        count = processed + i
        print("{}. {}".format(count + 1, id))
        url = f"https://www.molport.com/shop/compound/{id}"
        
        driver = webdriver.Firefox(options=options)
        timeout = 30

        with driver:
            driver.get(url)
            
            # Set timeout time 
            element_present = EC.presence_of_element_located((By.CLASS_NAME, "col-lg-6"))
            WebDriverWait(driver, timeout).until(element_present)
            
            soup = BeautifulSoup(driver.page_source, features="html.parser")
            driver.close()
            
        try:
            df.loc[count, "name"] = soup.find_all("h1", class_="my-0 py-0 h3")[0].get_text()
            contents = soup.find_all("div", class_="col-lg-6")[0]

            for row in contents.find_all("div", class_="row")[1:]:
                k = row.find_all("div")[0].get_text().strip(" \n")
                if k == "Molecular Weight":
                    df.loc[count, "weight"] = row.find_all("div")[1].get_text().strip(" \n")
                if k == "Molecular Formula":
                    df.loc[count, "chemical_formula"] = row.find_all("div")[1].get_text().strip(" \n")
                if k == "InChI Key":
                    df.loc[count, "InChIKey"] = row.find_all("span")[0].get_text().strip(" \n")
        
        except IndexError:
            df.loc[count, "name"] = "Error"
                
        df.to_csv(savepath, sep="\t", index=False)
        
    return df


def crawl_drugcentral(entities, savepath):
    os.makedirs(os.path.dirname(savepath), exist_ok=True)
    
    if os.path.isfile(savepath):
        df = pd.read_csv(savepath, sep="\t")
    else:
        df = entities[entities.entity.str.contains("Compound::drugcentral")]
        df["entity_id"] = df["entity"].str.split("::", expand=True)[1].str.split(
            ":", expand=True
        )[1]
        print("Number of compounds: {}".format(len(df)))
        df = df[["entity", "entity_id"]].reset_index(drop=True)
        df["InChI"] = None

    print("Total: {}".format(len(df)))
    processed = len(df[~df.InChI.isna()])
    print("Processed: {}".format(processed))
    print("Need to process: {}".format(len(df) - processed))

    for i, id in enumerate(df.entity_id.tolist()[processed:]):
        count = processed + i
        print("{}. {}".format(count + 1, id))
        doc = requests.get(f"https://drugcentral.org/drug/{id}/inchi", allow_redirects=True).content
        
        df.loc[count, "InChI"] = doc.decode("utf-8") 
        
        df.to_csv(savepath, sep="\t", index=False)
        
    return df


def crawl_bindingdb(entities, savepath):
    os.makedirs(os.path.dirname(savepath), exist_ok=True)
    
    if os.path.isfile(savepath):
        df = pd.read_csv(savepath, sep="\t")
    else:
        df = entities[entities.entity.str.contains("Compound::bindingdb")]
        df["entity_id"] = df["entity"].str.split("::", expand=True)[1].str.split(
            ":", expand=True
        )[1]
        df = df[["entity", "entity_id"]].reset_index(drop=True)
        df["InChIKey"] = None

    print("Total: {}".format(len(df)))
    processed = len(df[~df.InChIKey.isna()])
    print("Processed: {}".format(processed))
    print("Need to process: {}".format(len(df) - processed))

    for i, id in enumerate(df.entity_id.tolist()[processed:]):
        count = processed + i
        print("{}. {}".format(count + 1, id))
        
        doc = requests.get(f"https://www.bindingdb.org/bind/chemsearch/marvin/MolStructure.jsp?monomerid={id}", allow_redirects=True).content
        soup = BeautifulSoup(doc)
        
        contents = soup.find_all("div", class_="content_index")[0].find_all(
            "div")[0].find_all("p")

        for row in contents:
            k = row.find_all("b")[0].get_text()
            if k == "InChI Key":
                value = re.sub(r"^InChIKey=", "", row.find_all("span")[0].get_text())
                if value == "": value = "Error"
                df.loc[count, "InChIKey"] = value
                
        df.to_csv(savepath, sep="\t", index=False)

    return df


def crawl_hmdb(entities, savepath):
    os.makedirs(os.path.dirname(savepath), exist_ok=True)

    if os.path.isfile(savepath):
        df = pd.read_csv(savepath, sep="\t")
    else:
        df = entities[entities.entity.str.contains("Compound::hmdb")]
        df["entity_id"] = df["entity"].str.split("::", expand=True)[1].str.split(
            ":", expand=True)[1]
        print("Number of compounds: {}".format(len(df)))
        df = df[["entity", "entity_id"]].reset_index(drop=True)
        df["name"] = None
        df["InChIKey"] = None

    print("Total: {}".format(len(df)))
    processed = len(df[~df.InChIKey.isna()])
    print("Processed: {}".format(processed))
    print("Need to process: {}".format(len(df) - processed))

    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')

    for i, id in enumerate(df.entity_id.tolist()[processed:]):
        count = processed + i
        print("{}. {}".format(count + 1, id))
        doc = requests.get(f"https://hmdb.ca/metabolites/{id}", allow_redirects=True).content
        soup = BeautifulSoup(doc) 
        
        try:
            contents = soup.find_all("main")[0].find_all("table")[0].find_all("tr")

            for row in contents:
                try:
                    if row.find_all("th")[0].get_text() == "Common Name":
                        df.loc[count, "name"] = row.find_all("td")[0].get_text()
                    if row.find_all("th")[0].get_text() == "InChI Key":
                        df.loc[count, "InChIKey"] = row.find_all("td")[0].get_text()
                except:
                    pass
        except:
            df.loc[count, "name"] = "Error"
            df.loc[count, "InChIKey"] = "Error"
        
        df.to_csv(savepath, sep="\t", index=False)
        
    return df


def crawl_brenda(entities, savepath):
    os.makedirs(os.path.dirname(savepath), exist_ok=True)

    if os.path.isfile(savepath):
        df = pd.read_csv(savepath, sep="\t")
    else:
        df = entities[entities.entity.str.contains("Compound::brenda")]
        df["entity_id"] = df["entity"].str.split("::", expand=True)[1].str.split(
            ":", expand=True)[1]
        df = df[["entity", "entity_id"]].reset_index(drop=True)
        df["name"] = None
        df["InChIKey"] = None
        df["chemical_formula"] = None

    print("Total: {}".format(len(df)))
    processed = len(df[~df.InChIKey.isna()])
    print("Processed: {}".format(processed))
    print("Need to process: {}".format(len(df) - processed))

    for i, id in enumerate(df.entity_id.tolist()[processed:]):
        count = processed + i
        print("{}. {}".format(count + 1, id))
        if id == 21348:
            df.loc[count, "InChIKey"] = "Error"
            df.loc[count, "chemical_formula"] = "Error"
            df.loc[count, "name"] = "Error"
        else:
            doc = requests.get(f"https://www.brenda-enzymes.org/ligand.php?brenda%20ligand%20id={id}", 
                            allow_redirects=True,
                            timeout=30).content
            soup = BeautifulSoup(doc) 
            
            contents = soup.find_all("div", class_="equal")[0]
            ks = contents.find_all("div", class_="header")
            vs = contents.find_all("div", class_="cell")

            for j in range(len(ks)):
                if ks[j].get_text() == "Molecular Formula":
                    df.loc[count, "chemical_formula"] = vs[j].get_text()
                if ks[j].get_text() == "BRENDA Name":
                    df.loc[count, "name"] = vs[j].get_text()
                if ks[j].get_text() == "InChIKey":
                    df.loc[count, "InChIKey"] = vs[j].get_text()
        
        df.to_csv(savepath, sep="\t", index=False)
        
    return df