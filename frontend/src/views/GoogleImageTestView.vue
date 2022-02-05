<template>
    <div>
        googleimagetestview
        <b-form @submit.stop.prevent="googleSearch">
            <b-button type="submit" variant="primary">Google Search</b-button>
        </b-form>
        <b/>
        fetch prods
        <b-form @submit.stop.prevent="fetchProds">
            <b-button type="submit" variant="primary">Fetch Prods</b-button>
        </b-form>

        <b-form-input placeholder="Marca" v-model="marca"></b-form-input>
        <div class="mt-2">Value: {{ marca }}</div>
        <b-form-input placeholder="Referência" v-model="ref"></b-form-input>
        <div class="mt-2">Value: {{ ref }}</div>
        <b-form-input placeholder="Cor" v-model="cor"></b-form-input>
        <div class="mt-2">Value: {{ cor }}</div>

        <!--        <img :src="this.image"/>-->
        <img :src="image_url"/>

    </div>
</template>

<script>
    import axios from 'axios'


    export default {
        name: "GoogleImageTestView",
        data: function () {
            return {
                marca: "nike",
                ref: "646433",
                cor: "branco",
                response_test: '',
                image: '',
                image_url: ''
                // image_url: 'https://cdnv2.moovin.com.br/awallon/imagens/produtos/original/tenis-indoor-nike-beco-2-646433-006-pretocinza-d08805a4eb85e50a4092cd4474284a95.jpg'
            }
        },
        methods: {
            fetchProds() {
                // const query  = ''
                // const path = `/api/fetch/produtos/`
                const path = `http://localhost/api/comissao/2022-01-03/2022-01-03`
                // const path = `/api/testecosia/${query}`
                axios.get(path)
                    .then((res) => {
                        console.log(res)
                        console.log('deu certo em partes')
                        // this.image = res.data
                        this.image = "data:image/jpg;base64," + res.data.img
                    })
                    .catch((error) => {
                        // eslint-disable-next-line
                        console.error(error)
                    })
            },
            async googleSearch() {
                const base_path = `https://www.googleapis.com/customsearch/v1?key=AIzaSyAxkljtWwOvBkyVgaCgQQYR2bgFMUdzrQs&cx=f5c6bf2ce19682bb8&&searchType=image&&num=1&q=`

                const query = this.marca + '+' + this.ref + '+' + this.cor
                const path = base_path + query

                this.image_url = await axios.get(path)
                    .then((response) => {
                        console.log(response)
                        return response.data.items.map((item) => {
                            return item.link
                        });
                    })
                    .catch((error) => {
                        console.log(error)
                    })
                // const imagesUrl = 'https://cdnv2.moovin.com.br/awallon/imagens/produtos/original/tenis-indoor-nike-beco-2-646433-006-pretocinza-d08805a4eb85e50a4092cd4474284a95.jpg'
                // this.image_url = imagesUrl
                const api_path = `/api/produtos/images/`

                const produto = {nom_marca:this.marca, cod_referencia:this.ref, des_cor:this.cor, img:this.image_url[0]}
                console.log(produto)
                axios.put(api_path, produto)
                    .then((res) => {
                        console.log('axios.put')
                        console.log(res)
                    })
                    .catch((error) => {
                        console.log(error)
                    })
                return this.image_url
            }
        }
    }
</script>

<style scoped>

</style>