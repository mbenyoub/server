<html>
    <head>
        <style type="text/css">
                ${css}
            
            .header {
                width: 80%;
                margin-left: 80px;
            }
            
            .date {
                float: right;
                margin-right: 30px;
            }
            
            .text_content {
                margin-top: 30px;
            }
            
            .firma {
                margin-top: 120px;
            }
            
            .firma1 {
                float: left;
                width: 250px;
                text-align:center;
                border-top: 1px solid;
                margin-left: 50px;
            }
            .firma2 {
                float: right;
                width: 250px;
                text-align:center;
                border-top: 1px solid;
                margin-right: 100px;
            }
        </style>
    </head>
    <body>
        <div class="header" align="center">
            <%
                def carriage_returns(text):
                    return text.replace('\n', '<br />')
            %>
            <div>
                ${helper.embed_logo_by_name('camptocamp_logo', None, height=150)|n}
            </div>
            % for delivery in objects:
                <div>
                    ${delivery.image| n} <br/><br/>
                    ${helper.embed_logo_by_name('camptocamp_logo', None, height=150)|n} <br/><br/>
                    ${helper.embed_image('jpeg',str(delivery.program_id.user_id.company_id.logo),680)}  <br/><br/>
                    ${helper.embed_image('jpeg',str(delivery.image),680)}  <br/><br/>
                </div>
                <% setLang(delivery.partner_id.lang) %>
                % if formatLang(delivery.date, date=True):
                    <div class="date">Fecha Entrega: ${formatLang(delivery.date, date=True)}</div>
                % endif
                <h1>Entrega de Programa Social</h1>
                <h2> Programa: ${delivery.program_id.name} (${delivery.program_id.code})</h2>
                
                <div class="text_content">
                    <tr>
                    Se hace entrega de ${delivery.qty} - ${delivery.product_id.name}
                    a "
                    % if delivery.partner_id.title.id:
                        ${delivery.partner_id.title.name}
                    % endif
                    ${delivery.name}" (Curp: ${delivery.curp}), por parte del programa ${delivery.program_id.name} del municipio de zapopan
                    en la direccion ${delivery.program_id.direction_id.name}.
                </div>
                <br>
                <br>
                Attentamente:
                <div class="firma">
                    <div class="firma1">
                        ${delivery.program_id.user_id.name} <br>
                        Encargado del programa social otorgado
                    </div>
                    <div class="firma2">
                        % if delivery.partner_id.title.id:
                            ${delivery.partner_id.title.name}
                        % endif
                        ${delivery.name} <br>
                        Presente
                    <div>
                </div>
            % endfor
        </div>
    </body>
</html>
