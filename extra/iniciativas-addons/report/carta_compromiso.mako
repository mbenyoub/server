<html>
 <head>
  <style>
   ${css}
    .firma_container{
        padding: 0px 65px; 
	height:120px;
    }
    .firma_cds{
        float: left;
        padding-right: 15px;
        text-align: center;
    }
     .cuadro_cds{
         border: solid 1px;
        border-radius: 4px;
        padding: 49px 30px 6px 30px;
        width: 200px;
    }
    .cuadro_cliente{
         border: solid 1px;
        border-radius: 4px;
        padding: 49px 30px 24px 30px;
        width: 200px;
    }

	.content_font{
	 font-size: 13px;
	}
body{
font-size: 13px;
}

.title{
font-size: 16px !important;
}
 </style>
 </head>

 <body>
      %for o in objects :
        <% setLang(user.lang) %>
	<br>
	<div style="text-align: right;">Cuidad de Zapopan, Jalisco, M&eacute;xico a los ${getDay()} d&iacute;as de ${getMonth()} de ${getYear()} </div>
	<br>
	<div class="title"><b>CDS Autom&aacute;tico S de RL de CV </b></div>
	<div><b>Ganaderos #5683</div>
	<div>Col. Arcos Guadalupe, CP: 45037</div>
	<div>Zapopan, Jalisco, M&eacute;xico.</b></div>
	<br>
	<div><b>Tipo de proyecto: ${o.project_type.name or ''} </b></div>
	<div><b>Proyecto: ${o.name or ''}</b></div>
	<br>
  	%if (o.description_project) is not False:
        	<div class="content_font"> ${  (o.description_project).replace("\n", "<br/>") or ''}</div>
	%endif
	<br>
        <div><b>Acuerdos con el Cliente</b></div>
	<div class="content_font">${o.agreements or ''} </div>
	<br>
        <div><b>Promesas</b></div>
        <div class="content_font">${o.promises or ''} </div>
	<br/>
	<div>Por todo esto y m&aacute;s en CDS Autom&aacute;tico estamos m&aacute;s cerca de ti.</div>
	<br>
	<br>
	<div style="width:100%">	
		<div class="firma_container">
                    <div class="firma_cds">
                        <div class="cuadro_cds"> ${o.user_id.partner_id.name or ''} </div>
                        <br>
                            Nombre y Firma CDS
                    </div>
                    <div class="firma_cds">
                        <div class="cuadro_cliente"></div>
                        <br>
                            Nombre y Firma del Cliente
                    </div>
                </div>  
	<div>
     %endfor
 </body>
</html>

