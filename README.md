
Projeto para usar a magic formula do joel greenblat.

DISCLAIMER: não utilizar como base de investimentos, não me responsabilizo pelos resultados, não é uma recomendação.

# criação do ambiente
Essa aplicação usa 3 containers para a sua execução, um para o redis, um para o serviço e um para a api.
```bash
$ sh build_and_run.sh
```

Caso queira rodar ou reiniciar apenas um container existem arquivos individuais para isso, basta executar o comando abaixo.
```bash
$ sh start_api_container.sh
$ sh start_service_container.sh
$ sh start_redis_container.sh
```
ambos os containers usam a mesma imagem que é criada no script build_image.sh, ele é executado automaticamente no build_and_run.sh

# uso
Abaixo segue um exemplo de como fazer o request para api criada.
```bash
$ curl -X 'GET' \
  'http://0.0.0.0:8090/?number_of_stocks=150&min_ebit=1&min_market_cap=0&roic_ignore=0&format=json&graham_max_pl=15&graham_max_pvp=1.5&indexes=IBOV&indexes=BRX50' \
  -H 'accept: application/json'
```


# Referencias
Para capturar as informações do status invest eu me baseei no projeto [lfreneda/statusinvest](https://github.com/lfreneda/statusinvest), credito para eles pois a parte do status invest é uma versão adaptada desse projeto, so que em python. Fica o meu agradecimento.

# documentação
Existem informações sobre como usar no endpoint `/api/docs/` com os parametros que podem ser usados e o que cada um faz.

