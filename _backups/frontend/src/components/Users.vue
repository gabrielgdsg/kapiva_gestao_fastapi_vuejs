<template>
    <div>
        <h1>User List</h1>
        <table class="table table-hover">
            <thead>
            <tr>
                <td>ID</td>
                <td>Email</td>
                <td>Items</td>
            </tr>
            </thead>
            <tbody>
            <tr v-for="user in users" :key="user.id">
<!--                <td>{{ user.id }}</td>-->
<!--                <td>{{ user.email }}</td>-->
                <li>{{ user}}</li>
                <td>
                    <button class="btn btn-danger" v-on:click="deleteUser(user.id)">Delete</button>
                </td>
            </tr>
            </tbody>
        </table>
    </div>
</template>

<script>

    export default {
        name: "Users",
        data() {
            return {
                users: []
            }
        },
        created: function () {
            this.fetchUsers()
        },
        methods: {
            fetchUsers() {
                // let uri = 'http://localhost:80/users'
                let uri = '/api/comissao'
                this.axios.get(uri).then((response) => {
                    console.log(response)
                    this.users = response.data
                })
            },
            deleteUser(id) {
                let uri = `/api/users/${id}`
                // let uri = `http://localhost:80/users/${id}`
                let index = this.users.map((x) => {
                    return x.id
                }).indexOf(id)
                this.axios.delete(uri).then(
                    this.users.splice(index, 1)
                )
            }
        }
    }
</script>

<style scoped>

</style>