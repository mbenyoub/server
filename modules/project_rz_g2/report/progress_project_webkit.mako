<html>
    <head>
        <style type="text/css">
                ${css}
            
            .text_content {
                font-weight: normal;
                font-size: 11px;
                text-align: left;
            }
            
            .text_bold {
                font-weight: bold;
                font-size: 11px;
                text-align: left;
                margin-right: 10px;
            }
            
            .text_title {
                font-weight: bold;
                font-size: 20px;
            }
            
            .text_subtitle {
                font-weight: bold;
                font-size: 14px;
                text-align: center;
            }
            
            .table_header {
                font-weight: bold;
                font-size: 11px;
                text-align: center;
                background-color: #EEEEEE;
                padding: 2px;
            }
            
            .barcode {
                background-color: #6492C5;
                text-color: #FFFFFF;
                font-size: 9px;
                margin: 2px;
                padding: 2px;
                text-align: center;
            }
            
            .barcode2 {
                background-color: #D1D1D1;
                text-color: #000000;
                font-size: 9px;
                margin: 2px;
                padding: 2px;
                text-align: center;
            }
            
        </style>
    </head>
    <body>
        <div class="header" align="center" style="width:100%;">
            <%
                def carriage_returns(text):
                    return text.replace('\n', '<br />')
                    
            %>
            % for project in objects:
                <% setLang(project.user_id.partner_id.lang) %>
                <div style="width:100%;">
                    <table>
                        <tr>
                            <td>${helper.embed_image('jpeg',str(project.user_id.company_id.logo),160)|n}</td>
                            <td><span class="text_title">PLAN DE SEGUIMIENTO RETO ZAPOPAN</span></td>
                        </tr>
                    </table>
                </div>
                <div style="width:80%;margin-bottom:25px;">
                    <div style="margin-right:25px;float:left;">
                        <table>
                            <tr>
                                <th class="text_bold">Nombre del Proyecto:</th>
                                <th class="text_content">${project.name}</th>
                            </tr>
                            <tr>
                                <th class="text_bold">Codigo:</th>
                                <th class="text_content">${project.code}</th>
                            </tr>
                        </table>
                    </div>
                    <div style="margin-right:25px;">
                        <table>
                            <tr>
                                <th class="text_bold">Emprendedor:</th>
                                <th class="text_content">${project.partner_id.name}</th>
                            </tr>
                            <tr>
                                <th class="text_bold">Evaluador:</th>
                                <th class="text_content">${project.user_id.name}</th>
                            </tr>
                        </table>
                    </div>
                </div>
                <div style="width:75%;">
                    <span class="text_subtitle">RESULTADO EVALUACION</span>
                    <table >
                        <tr style="border-bottom: 1px solid; padding-bottom: 3px;">
                            <td class="text_bold" style="width:40%;">Resultado Total</td>
                            <td class="text_content" width="250px">
                                <div class="barcode" >${project.res_performance}%</div>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="2">
                                <table>
                                    <tr>
                                        <th class="table_header">Categoria</th>
                                        <th class="table_header">Peso especifico</th>
                                        <th class="table_header">Nivel de Desempeño</th>
                                    </tr>
                                    % for eval in project.evaluation_project_ids:
                                        <tr>
                                            <td class="text_content">${eval.category_id.name}</td>
                                            <td class="text_content">${eval.porcentage}</td>
                                            <td width="250px"> <div class="barcode2" >${eval.performance}%</div></td>
                                        </tr>
                                    % endfor
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td class="text_bold" style="width:40%;">Desempeño Proyecto</td>
                            <td class="text_content" width="250px">
                                <div class="barcode" >${project.res_project_performance}%</div>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="2">
                                <table>
                                    <tr>
                                        <th class="table_header">Categoria</th>
                                        <th class="table_header">Peso especifico</th>
                                        <th class="table_header">Nivel de Desempeño</th>
                                    </tr>
                                    % for eval in project.evaluation_partner_ids:
                                        <tr>
                                            <td class="text_content">${eval.category_id.name}</td>
                                            <td class="text_content">${eval.porcentage}</td>
                                            <td width="250px"> <div class="barcode2" >${eval.performance}%</div></td>
                                        </tr>
                                    % endfor
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td class="text_bold" style="width:40%;">Desempeño Emprendedor</td>
                            <td class="text_content" width="250px">
                                <div class="barcode" >${project.res_partner_performance}%</div>
                            </td>
                        </tr>
                    </table>
                </div>
                <br/>
                <br/>
                <div>
                    <span class="text_subtitle">PLAN DE SEGUIMIENTO</span>
                    <br/>
                    % for phase in project.phase_ids:
                        <br/>
                        <table >
                            <tr>
                                <th class="table_header">Etapa</th>
                                <th class="table_header">Tema</th>
                                <th class="table_header">Entregables</th>
                            </tr>
                            <tr>
                                <td class="text_content" >${phase.sequence}</td>
                                <td class="text_content" >
                                    <div class="text_bold">${phase.name}</div>
                                    <div>
                                        <table >
                                            <tr>
                                                <th class="table_header">Fecha inicio</th>
                                                <th class="table_header">Fecha fin</th>
                                                <th class="table_header">Horas sugeridas consultoria</th>
                                            </tr>
                                            <tr>
                                                <td class="text_content">${phase.date_start}</td>
                                                <td class="text_content">${phase.date_end}</td>
                                                <td class="text_content">${phase.meeting_time}</td>
                                            </tr>
                                        </table>
                                    </div>
                                </td>
                                <td class="text_content">
                                    <table >
                                        <tr>
                                            <th class="table_header">#</th>
                                            <th class="table_header">Nombre</th>
                                            <th class="table_header">Estado</th>
                                        </tr>                                        
                                        % for task in phase.task_ids:
                                            <tr>
                                                <td class="text_content">${task.sequence}</td>
                                                <td class="text_content">${task.name}</td>
                                                <td class="text_content">${task.stage_id.name}</td>
                                            </tr>
                                        % endfor
                                    </table>
                                </td>
                            </tr>
                        </table>
                    % endfor
                </div>
            % endfor
        </div>
    </body>
</html>
