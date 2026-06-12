from . import elobservador, elpais, montevideo, ladiaria

COLLECTORS = {
    "elobservador": elobservador.collect,
    "elpais": elpais.collect,
    "montevideo": montevideo.collect,
    "ladiaria": ladiaria.collect,
}
