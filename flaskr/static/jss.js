<script type="text/javascript">

    function updateContentLen(content){
        var str = content.value;

        var len=0;
        for(var i=0;i<str.length;i++){
            if(  str.charAt(i).match(/[^\x00-\xff]/ig) !=null) {
                len += 2;
            }else{
                len += 1;
            }
        }

        var clen =(140-len);

        document.getElementById("checklen").innerHTML = clen;

    }

</script>