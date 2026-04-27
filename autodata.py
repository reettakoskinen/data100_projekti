import pandas as pd
import json
import sqlite3

# Lue CSV
df = pd.read_csv(
    "TieliikenneAvoinData_31_12_2025.csv",
    sep=";", 
    encoding="latin1",
    low_memory=False
)

# Datan karsinta
df["kayttovoima"] = pd.to_numeric(df["kayttovoima"], errors="coerce")
df["ajoneuvonkaytto"] = pd.to_numeric(df["ajoneuvonkaytto"], errors="coerce")

df = df[
    (df["ajoneuvoluokka"].isin(["M1", "M1G"])) &
    (df["ajoneuvonkaytto"] == 1) &
    (df["korityyppi"].isin(["AA", "AB", "AC", "AD", "AE", "1.7"])) &
    (df["kayttovoima"].notna())
]

# Valitse sarakkeet
cols = [
    "ensirekisterointipvm", "kayttoonottopvm", "vari",
    "omamassa", "ajonKokPituus", "ajonLeveys",
    "kayttovoima", "merkkiSelvakielinen",
    "mallimerkinta", "kaupallinenNimi",
    "kunta", "NEDC_Co2", "matkamittarilukema"
]

df = df[cols]

# Korvaa kuntakoodit nimellä
with open("kuntarajat.json", encoding="utf-8") as f:
    kuntadata = json.load(f)

kunta_map = {}
for feat in kuntadata["features"]:
    prop = feat["properties"]
    kunta_map[int(prop["NATCODE"])] = prop["NAMEFIN"]

df["kunta"] = df["kunta"].map(kunta_map)

# Poista rivit joista kunta puuttuu
df = df[df["kunta"].notna()]

# Korjaa päivämäärät
df["ensirekisterointipvm"] = pd.to_datetime(
    df["ensirekisterointipvm"],
    format="%d.%m.%Y",
    errors="coerce"
)
df["kayttoonottopvm"] = pd.to_datetime(
    df["kayttoonottopvm"]
    .astype(str)
    .str.replace("0000$", "0101", regex=True),
    format="%Y%m%d",
    errors="coerce"
)
df = df[
    df["ensirekisterointipvm"].notna() &
    df["kayttoonottopvm"].notna()
]

# CO2 sähköautoille
df.loc[df["kayttovoima"] == 4, "NEDC_Co2"] = 0

# pd.NA puuttuville väri arvoille
df["vari"] = df["vari"].replace(-1, pd.NA)

# Merkki-korjaukset
df.loc[
    df["kaupallinenNimi"].isin(["SEBRING", "CROSSFIRE"]),
    "merkkiSelvakielinen"
] = "Chrysler"

df.loc[
    (df["kaupallinenNimi"] == "XJ") &
    (df["merkkiSelvakielinen"] == "Daimler"),
    "merkkiSelvakielinen"
] = "Jaguar"

replace_map = {
    "AUBURN": "Auburn",
    "ADLER": "Adler",
    "QUATTRO": "Audi",
    "Quattro": "Audi",
    "AUDI AG": "Audi",
    "BINZ": "Binz",
    "ALPINA": "BMW",
    "Alpina": "BMW",
    "BMW Alpina": "BMW",
    "BMW i": "BMW",
    "BWW": "BMW",
    "CATERHAM": "Caterham",
    "DESOTO": "DeSoto",
    "De Soto": "DeSoto",
    "DE SOTO": "DeSoto",
    "DE LOREAN": "De Lorean",
    "GM Daewoo": "Daewoo",
    "EDSEL": "Edsel",
    "FORD-CNG-TECHNIK": "Ford",
    "Ford-TEC": "Ford",
    "HUDSON": "Hudson",
    "HUMBER": "Humber",
    "HUPMOBILE": "Hupmobile",
    "Hundai": "Hyundai",
    "Jaguar Land Rover Limited": "Jaguar",
    "JENSEN": "Jensen",
    "KAISER": "Kaiser",
    "Lada-Vaz": "Lada",
    "Niva": "Lada",
    "DaimlerChrysler": "Mercedes-Benz",
    "Daimler": "Mercedes-Benz",
    "MERCEDES-AMG": "Mercedes-Benz",
    "Mercedes-AMG": "Mercedes-Benz",
    "Mercedes-Benz-CI": "Mercedes-Benz",
    "NASH": "Nash",
    "BMW MINI": "Mini",
    "MORGAN": "Morgan",
    "POLESTAR": "Polestar",
    "SALEEN": "Saleen",
    "SKD": "Skoda",
    "Skida": "Skoda",
    "STUTZ": "Stutz",
    "SINGER": "Singer",
    "TESLA MOTORS": "Tesla",
    "Tesla Motors": "Tesla",
    "THINK": "Think",
    "VOLKSWAGEN": "Volkswagen",
    "VW": "Volkswagen",
    "Volkswagen, VW": "Volkswagen",
    "VOLKSWAGEN AG": "Volkswagen",
    "Volkswagen-Karmann": "Volkswagen",
    "VOLKSWAGEN-BEA": "Volkswagen",
    "PANHARD": "Panhard",
    "Polster": "Polestar",
    "glas": "Glas",
    "commer": "Commer",
    "ASTON MARTIN": "Aston Martin",
    "INFINITI": "Infiniti",
    "STANDARD": "Standard",
    "DAIMLER-BENZ": "Mercedes-Benz",
    "Mercedes-Benz-Adriatik": "Mercedes-Benz",
    "MERCEDES BENZ": "Mercedes-Benz",
    "MB": "Mercedes-Benz",
    "PACKARD": "Packard",
    "VW-Porsche": "Porsche",
    "Audi-Porsche": "Porsche",
    "STUDEBAKER": "Studebaker",
    "FORD MERCURY": "Ford",
    "FORD MUSTANG": "Ford",
    "Dodge-Brothers": "Dodge",
    "Renault-Dacia": "Renault",
    "TOYOTA": "Toyota",
    "TOYOTA MOTORSPORT": "Toyota",
    "TOYOPET": "Toyota",
    "toyota": "Toyota",
    "Range-Rover": "Land Rover",
    "Chrysler-Sunbeam": "Chrysler",
    "Sunbeam Talbot": "Chrysler",
    "Sunbeam": "Chrysler",
    "Chrysler-Simca": "Chrysler",
    "SIMCA / FIAT": "Fiat",
    "Fiat-Bertone": "Fiat",
    "Seat-Fiat": "Fiat",
    "VAZ": "Lada",
    "Vaz": "Lada",
    "LYNK&CO": "Lynk&Co", 
    "LYNK AND CO": "Lynk&Co"
}

df["merkkiSelvakielinen"] = df["merkkiSelvakielinen"].replace(replace_map)

# Testitulostus
pd.set_option('display.max_columns', None)
# print(list(df["merkkiSelvakielinen"].unique()))
# print(df.head())

# Kirjoita sql tiedostoon
conn = sqlite3.connect("autodata.db")
df.to_sql("autot", conn, if_exists="replace", index=False)
conn.close()

# testi tulostus autodata.db tiedoston tarkistamiseen (poista ennen palautusta)
conn = sqlite3.connect("autodata.db")
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
# print("autodata.db:")
# print(tables)
# df = pd.read_sql("SELECT * FROM autot LIMIT 5;", conn)
# print(df)