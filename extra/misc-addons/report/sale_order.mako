<html>
 <head>
  <style>
   ${css}
   .titles_0{
       font-size: 12px;
       font-weight: bold;
   }
      .content{
          font-size: 12px;
          text-align: left;
      }
      .table td{
            /*border: solid 1px;*/
            width:10%;

      }
      .table tr{
          /*border: solid 1px;*/
      }
      .table{
          width: 100%;
      }

      table{
          font-size: 11px;
          width: 100%;
      }
      .main_title{
            width: 100%;
            background-color: #B0C4DE;
            text-align: center;
            font-size: 21px;
            font-weight: bold;
            padding: 10px 0px;
        }
        .title{
            text-align: center;
            font-size: 22px;
            font-weight: bold;
        }
        .address{
            text-align: center;
            font-size: 16px;

        }
        .space_40{
            margin: 40px;
            }
       .title_zone{
            text-align: left;
            font-size: 12px;
            font-weight: bold;
        }
      .cell_1{
        padding-left: 30px;
        text-align: center;
        font-size: 11px;
        font-weight: bold;
        width: 110px;
      }
      .cell_2{
        font-size: 11px;
        font-weight: bold;
        width: 295px;
        text-align: center;

      }
      .cell_3{
          padding-right: 10px;
          text-align: center;
          font-size: 11px;
          font-weight: bold;
          width: 70px;
      }
      .cell_4{
            padding-right: 10px;
          text-align: right;
          font-size: 11px;
          font-weight: bold;
          width: 80px;
      }

      .cell_5{

        text-align: center;
        font-size: 11px;
        width: 50px;
      }
      .cell_6{
        font-size: 11px;
        width: 355px;

        text-align: center;
      }
      .cell_7{
          padding-right: 10px;
          text-align: center;
          font-size: 11px;
          width: 70px;

      }
      .cell_8{
            padding-right: 10px;
          text-align: right;
          font-size: 11px;
          width: 80px;

      }
  </style>
 </head>

 <body>

%for o in objects :
            <% setLang(user.lang) %>
<div style="margin:30px;"></div>

<div class="main_title"></div>
    <br/><br/>
<div style="margin:auto">
        <br/><br/><br/><br/>
        <div class="title"> PLANICA </div>
        <br/><br/>
        <div class="title"> PRESENTADO POR  </div>
        <div class="space_40"></div>
        <div style="text-align:center;" >
            <br/>
        </div>
         <br/><br/>
        <div style="text-align:center;" >
            <span class="title">Plánica Audiovideo, S.A. de C.V.</span>
            <p class="address">Montecito 38 piso 22 Ofc. 01<br/>
                Col. Napoles Del. Benito Juárez<br/>
                México, Distrito Federal 03810<br/>
                90003300 ext 44 <br/></p>
        </div>
</div>

<div style="margin:220px;"></div>
<br/>


  <table style="width:100%">
      <tr>
         <td class='cell_1'>Cantidad</td>
         <td class='cell_2'>Descripcion</td>
           <td class='cell_3'>Desc.</td>
          <td class='cell_3'>Prec.<br/> Unit.</td>
          <td class='cell_3'>Prec. Unit.<br/> Desc</td>
         <td class='cell_4'>Totales</td>
          </tr>
      </table>



<br/>
<br/>

<table>
<tr>
    <td colspan=3 style='text-align:right;font-size: 13px;font-weight: bold;'> <b>SUB TOTAL: </b> </td>
    <td style='text-align:right;font-size: 13px;font-weight: bold;'> $  </td>
 </tr>

 <tr>
    <td colspan=3 style='text-align:right;font-size: 13px;font-weight: bold;'><b>IVA: </b></td>
    <td style='text-align:right;font-size: 13px;font-weight: bold;'> $  </td>
 </tr>

 <tr>
    <td colspan=3 style='text-align:right;font-size: 13px;font-weight: bold;'><b>TOTAL: </b></td>
    <td style='text-align:right;font-size: 13px;font-weight: bold;border-top:solid 1px'> $  </td>
 </tr>

</table>


<br/>
<br/>
<br/>
<br/>
<br/>
<br/>


 <table style="width:100%">
               <tr>
                <td colspan=3>Este presupuesto tiene vigencia de 30 d&iacute;as a partir de su expedici&oacute;n <br/><br/> </tr>
    <tr>
        <td style="border-top:solid 1px;"> Cliente: ${o.partner_id.name}</td>
        <td style='padding: 0px 15px'></td>
        <td style="border-top:solid 1px;"> Fecha</td>
    </tr>
    <tr><td style="padding:20px 5px"></td></tr>
    <tr style='padding-top:10px'>
        <td style="border-top:solid 1px;"> Contratista: Pl&aacute;nica Audiovideo, S.A. de C.V.</td>
        <td style='padding: 0px 15px'></td>
        <td style="border-top:solid 1px;"> Fecha</td>
    </tr>

</table>

<br/>
<br/>
 <table style="width:100%">
 <tr>
 <td style="border-bottom: solid 1px; text-align: left;"><b>Notas importantes </b></td>
 </tr>

 <tr>
 <td style="padding: 10px">${o.note or ''} </td>
 </tr>
 </table>
%endfor




 </body>
</html>
