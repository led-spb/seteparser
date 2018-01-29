#!/bin/sh
CUR_DIR=$(dirname $0)
. $CUR_DIR/.config
PARSER=$CUR_DIR/siteparser.py
OUTPUT="-o telegram -oo token $BOT_TOKEN target $TARGET"

#${PARSER} -p cps   -pp spec гинек -f regexp -ff Галынина ${OUTPUT} title 'Номерки к врачам' once timeout 64800
#${PARSER} -p kdc   -f regexp -ff Жукова ${OUTPUT} title 'Номерки к врачам' timeout 64800
#${PARSER} -p kdc   -pp dms 1 -f regexp -ff Гастроэнт ${OUTPUT} title 'Номерки к врачам' timeout 64800
#${PARSER} -p avito -pp city sankt-peterburg category tovary_dlya_detey_i_igrushki/detskie_kolyaski ${OUTPUT}

$PARSER -p css -pp \
  url http://school100spb.ru/ css 'article' template \
'<b>school100spb.ru</b>
{% for link in item.cssselect(".entry-title a") %}<a href="{{ link.get("href") }}">{{ link.text_content() }}</a>{% endfor %}
{% for text in item.cssselect(".entry-content p") %}{{ text.text }}{% endfor %}' \
$OUTPUT

${PARSER} -p css -pp \
  url http://oo-kalina.ru/ css '.blog .contentpaneopen' \
  template \
'<b>oo-kalina.ru</b>
{% for h in item.cssselect("h2") %}{% for link in h.cssselect("a") %}<a href="http://oo-kalina.ru{{ link.get("href") }}">{{ h.text_content()|regex_replace("\s{2,}"," ") }}</a>{% endfor %}{% endfor %}
{% for p in item.cssselect(".article-content") %}{{ p.text_content()|regex_replace("\s{2,}"," ") }}{{""}}{% endfor %}' \
$OUTPUT

