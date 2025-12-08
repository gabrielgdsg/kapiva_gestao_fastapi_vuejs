<template>
    <div class="editable">
        <div v-if="editable != false && numero==true">
            <currency-input v-model="comp_value"/>  <!-- using a custom template for number or R$ if needed-->
        </div>
        <div v-else-if="editable != false">
            <b-input v-model="comp_value"/> <!-- for not-number inputs-->
        </div>
        <div v-else-if="editable == false && numero==true">
            {{comp_value | numero}} <!-- for not-editable numbers -->
        </div>
        <div v-else>
            {{comp_value}} <!-- for not-editable texts-->
        </div>

    </div>

</template>

<script>
    export default {
        name: 'EditableField',
        props: ['editable', 'value', 'numero'],
        model: {
            prop: 'value',
            event: 'update:value'
        },
        computed: {
            comp_value: {
                get: function () {
                        return this.value
                },
                set: function (newValue) {
                    this.$emit('update:value', newValue);
                }
            }
        }
    }
</script>

<style scoped>
    /*copied style from a <b-input> element*/
    input {
        display: block;
        width: 100%;
        height: calc(1.5em + .75rem + 2px);
        padding: .375rem .75rem;
        font-size: 1rem;
        font-weight: 400;
        line-height: 1.5;
        color: #495057;
        background-color: #fff;
        background-clip: padding-box;
        border: 1px solid #ced4da;
        border-radius: .25rem;
        transition: border-color .15s ease-in-out, box-shadow .15s ease-in-out;
    }

</style>