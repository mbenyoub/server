<html>
    <head>
        <style type="text/css">
                ${css}
            
            .header {
                margin-top: -10px;
                width: 80%;
                margin-left: 80px;
                font-size: 16px;
            }
            
            .date {
                float: right;
                margin-right: 30px;
                margin-top: 10px;
            }
            
            .text_content {
                margin-top: 140px;
            }
            
            .text_bold {
                font-weight: bold;
            }
            
            .firma {
                margin-top: 60px;
                text-align:center;
            }
            
            .firma_text {
                width: 40%;
                margin-left: 30%;
                border-top: 1px solid;
                clear: both;
            }
        </style>
    </head>
    <body>
        <div class="header" align="center">
            <%
                def carriage_returns(text):
                    return text.replace('\n', '<br />')
            %>
            % for info in objects:
                <% setLang(info.database_id.partner_id.lang) %>
                % if info.date:
                    <div class="date">Guadalajara, Jalisco, México a ${info.date_string}</div>
                % endif
                <br/>
                <div>
                    <span class="text_bold">SF ERP, S.C.</span>
                </div>
                
                <div style="margin-top: 20px; float: right; width: 320px;">
                    <span class="text_bold">Asunto:</span>
                                Manifestacion de Conocimiento y Autorizacion de entrega de CFDI para que SFERP, S.C.
                                entregue al SAT, copia de los comprobantes  certificados.
                </div>
                <br/>
                <div class="text_content">
                    <tr>
                    ${info.response}, 
                    % if info.name != info.response:
                        en mi caracter de representante legal de 
                    % endif
                        % if info.regimen_fiscal_id:
                            ${info.regimen_fiscal_id.name}
                        % endif
                        ${info.name}
                     con registro federal de contribuyentes  ${info.vat}  y con
                    domicilio fiscal en ${info.street} ${info.l10n_mx_street3}
                    % if info.l10n_mx_street4:
                    -${info.l10n_mx_street4}
                    % endif
                     Col. ${info.street2} C.P. ${info.zip}, ${info.city}, ${info.state_id.name}, ${info.country_id.name};
                    con la finalidad de que la presente sirva como constancia de lo previsto en la regla I.2.7.2.7 de
                    la Resolucion Miscelanea Fiscal en vigor manifiesto que:
                    <br/>
                    <br/>
                    <div style="margin-left: 20px;">
                        I.  Haré uso de los servicios de SFERP, S.C. para la certificacion de Comprobantes
                        Fiscales Digitales  a través de Internet.
                        <br/>
                        II. Tengo conocimiento y autorizo a SFERP, S.C.  para que entregue al Servicio de
                        Administracion Tributaria, copia de los comprobantes fiscales que haya certificado
                        a mi representada en dicho servicio.
                    </div>
                    
                </div>
                <br>
                <br>
                <div class="firma">
                    <div style="margin-bottom: 60px;">Attentamente:</div>
                    <br/>
                    <div align="center" class="firma_text">
                        ${info.response} <br>
                        % if info.name != info.response:
                           Representante legal
                        % endif
                    </div>
                </div>
            % endfor
        </div>
    </body>
</html>
