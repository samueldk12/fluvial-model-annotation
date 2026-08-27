# -*- coding: utf-8 -*-
"""
Gerenciador de Conjuntos e Presets de Classes para Anotação em Múltiplos Domínios.
Suporta Naval, Urbano, Ambientes Fechados, Natureza, Objetos, Tatuagens e Digitais.
"""

import os
import json
import time

PRESET_NAUTICAL = {
    "id": "nautical_default",
    "domain": "naval",
    "name": "Classes Náuticas (Padrão)",
    "description": "Embarcações gerais, cargueiros, rebocadores, balsas, lanchas, veleiros e sinalizações marítimas.",
    "classes": [
        {"id": 0, "name": "embarcacao", "color": "#00f0ff"},
        {"id": 1, "name": "navio_cargueiro", "color": "#1890ff"},
        {"id": 2, "name": "rebocador", "color": "#fa8c16"},
        {"id": 3, "name": "balsa", "color": "#52c41a"},
        {"id": 4, "name": "lancha", "color": "#722ed1"},
        {"id": 5, "name": "veleiro", "color": "#eb2f96"},
        {"id": 6, "name": "boia_sinalizacao", "color": "#fadb14"},
        {"id": 7, "name": "outro", "color": "#8c8c8c"}
    ]
}

PRESET_ENVIRONMENT_SEGMENTATION = {
    "id": "environment_segmentation",
    "domain": "naval",
    "name": "Segmentação de Ambiente & Cenário (Água, Porto, Floresta)",
    "description": "Segmentação semântica e poligonal de elementos do ambiente naval e terrestre: água/mar/rio, porto/cais, floresta/vegetação, margens, construções e céu.",
    "classes": [
        {"id": 0, "name": "agua", "color": "#00f0ff"},
        {"id": 1, "name": "porto", "color": "#fa8c16"},
        {"id": 2, "name": "floresta", "color": "#52c41a"},
        {"id": 3, "name": "margem_solo", "color": "#a0d911"},
        {"id": 4, "name": "edificacao_urbana", "color": "#722ed1"},
        {"id": 5, "name": "ceu", "color": "#1890ff"},
        {"id": 6, "name": "praia_areia", "color": "#fadb14"},
        {"id": 7, "name": "obstaculo_maritimo", "color": "#ff4d4f"}
    ]
}

PRESET_PORT_SECURITY_PEOPLE = {
    "id": "port_security_people",
    "domain": "naval",
    "name": "Segurança Portuária & Pessoas (EPI)",
    "description": "Monitoramento de pessoas no cais, operadores com EPI, coletes salva-vidas, botes de resgate e pedestres em área de risco.",
    "classes": [
        {"id": 0, "name": "pessoa", "color": "#ff4d4f"},
        {"id": 1, "name": "operador_porto", "color": "#faad14"},
        {"id": 2, "name": "colete_salva_vidas", "color": "#52c41a"},
        {"id": 3, "name": "capacete_epi", "color": "#1890ff"},
        {"id": 4, "name": "bote_resgate", "color": "#13c2c2"},
        {"id": 5, "name": "veiculo_doca", "color": "#722ed1"},
        {"id": 6, "name": "pedestre_area_risco", "color": "#f5222d"}
    ]
}

PRESET_PORT_INFRASTRUCTURE = {
    "id": "port_infrastructure",
    "domain": "naval",
    "name": "Infraestrutura & Cais Portuário",
    "description": "Elementos de acostagem, guindastes portainers, defensas do cais, passarelas e obstáculos na água.",
    "classes": [
        {"id": 0, "name": "cais_atracacao", "color": "#1890ff"},
        {"id": 1, "name": "guindaste_portainer", "color": "#fa8c16"},
        {"id": 2, "name": "defensa_cais", "color": "#52c41a"},
        {"id": 3, "name": "passarela_embarque", "color": "#722ed1"},
        {"id": 4, "name": "boia_sinalizacao", "color": "#fadb14"},
        {"id": 5, "name": "obstaculo_agua", "color": "#ff4d4f"}
    ]
}

PRESET_URBAN_TRAFFIC = {
    "id": "urban_traffic",
    "domain": "urbano",
    "name": "Trânsito Urbano & Smart City",
    "description": "Veículos leves e pesados, motocicletas, ciclistas, pedestres, semáforos e sinalização viária.",
    "classes": [
        {"id": 0, "name": "carro", "color": "#1890ff"},
        {"id": 1, "name": "caminhao", "color": "#fa8c16"},
        {"id": 2, "name": "onibus", "color": "#722ed1"},
        {"id": 3, "name": "motocicleta", "color": "#eb2f96"},
        {"id": 4, "name": "bicicleta", "color": "#13c2c2"},
        {"id": 5, "name": "pedestre", "color": "#52c41a"},
        {"id": 6, "name": "semaforo", "color": "#fadb14"},
        {"id": 7, "name": "faixa_pedestre", "color": "#ffffff"},
        {"id": 8, "name": "placa_transito", "color": "#ff4d4f"}
    ]
}

PRESET_INDOOR_OFFICE = {
    "id": "indoor_office",
    "domain": "fechado",
    "name": "Ambientes Fechados & Ocupação",
    "description": "Ocupantes, estações de trabalho, portas, janelas, computadores e equipamentos de segurança.",
    "classes": [
        {"id": 0, "name": "pessoa", "color": "#ff4d4f"},
        {"id": 1, "name": "cadeira", "color": "#1890ff"},
        {"id": 2, "name": "mesa_trabalho", "color": "#fa8c16"},
        {"id": 3, "name": "sofa", "color": "#722ed1"},
        {"id": 4, "name": "porta", "color": "#52c41a"},
        {"id": 5, "name": "janela", "color": "#13c2c2"},
        {"id": 6, "name": "laptop_monitor", "color": "#eb2f96"},
        {"id": 7, "name": "camera_seguranca", "color": "#fadb14"},
        {"id": 8, "name": "extintor", "color": "#ff7875"}
    ]
}

PRESET_NATURE_WILDLIFE = {
    "id": "nature_wildlife",
    "domain": "natureza",
    "name": "Natureza & Vida Selvagem",
    "description": "Mamíferos, aves, répteis, vegetação florestal, rios, focos de calor/fogo e rastros.",
    "classes": [
        {"id": 0, "name": "mamifero_silvestre", "color": "#fa8c16"},
        {"id": 1, "name": "ave_passaro", "color": "#1890ff"},
        {"id": 2, "name": "reptil", "color": "#52c41a"},
        {"id": 3, "name": "arvore_copa", "color": "#389e0d"},
        {"id": 4, "name": "rio_corpo_dagua", "color": "#00f0ff"},
        {"id": 5, "name": "fogo_foco_calor", "color": "#ff4d4f"},
        {"id": 6, "name": "fumaca", "color": "#8c8c8c"},
        {"id": 7, "name": "pegada_rastro", "color": "#d48806"},
        {"id": 8, "name": "fauna_outro", "color": "#722ed1"}
    ]
}

PRESET_OBJECTS_INDUSTRY = {
    "id": "objects_industry",
    "domain": "objetos",
    "name": "Objetos & Varejo / Indústria",
    "description": "Caixas, ferramentas, frascos, pacotes, componentes eletrônicos e controle de qualidade.",
    "classes": [
        {"id": 0, "name": "caixa_embalagem", "color": "#fa8c16"},
        {"id": 1, "name": "ferramenta", "color": "#1890ff"},
        {"id": 2, "name": "garrafa_frasco", "color": "#13c2c2"},
        {"id": 3, "name": "pacote_produto", "color": "#52c41a"},
        {"id": 4, "name": "componente_eletronico", "color": "#722ed1"},
        {"id": 5, "name": "defeito_superficie", "color": "#ff4d4f"},
        {"id": 6, "name": "codigo_barras_etiqueta", "color": "#fadb14"},
        {"id": 7, "name": "objeto_geral", "color": "#d9d9d9"}
    ]
}

PRESET_TATTOO_STUDIO = {
    "id": "tattoo_studio",
    "domain": "tatuagens",
    "name": "Tatuagens & Arte Corporal",
    "description": "Estilos artísticos (Tribal, Oriental, Realismo, Old School, Blackwork), letterings e regiões dérmicas.",
    "classes": [
        {"id": 0, "name": "tatuagem_tribal", "color": "#000000"},
        {"id": 1, "name": "tatuagem_oriental", "color": "#eb2f96"},
        {"id": 2, "name": "tatuagem_realismo", "color": "#1890ff"},
        {"id": 3, "name": "tatuagem_oldschool", "color": "#fa8c16"},
        {"id": 4, "name": "tatuagem_blackwork", "color": "#722ed1"},
        {"id": 5, "name": "tatuagem_fineline", "color": "#13c2c2"},
        {"id": 6, "name": "escrita_lettering", "color": "#52c41a"},
        {"id": 7, "name": "braco_pele", "color": "#ffc069"},
        {"id": 8, "name": "costas_pele", "color": "#d48806"},
        {"id": 9, "name": "perna_pele", "color": "#adc6ff"}
    ]
}

PRESET_FINGERPRINTS_FORENSICS = {
    "id": "fingerprints_forensics",
    "domain": "digitais",
    "name": "Digitais & Papiloscopia Forense",
    "description": "Impressões digitais, padrões papilares (Verticilo, Presilha, Arco) e minúcias de Galton.",
    "classes": [
        {"id": 0, "name": "impressao_digital", "color": "#13c2c2"},
        {"id": 1, "name": "verticilo_whorl", "color": "#00f0ff"},
        {"id": 2, "name": "presilha_loop", "color": "#1890ff"},
        {"id": 3, "name": "arco_arch", "color": "#52c41a"},
        {"id": 4, "name": "minucia_bifurcacao", "color": "#fa8c16"},
        {"id": 5, "name": "minucia_terminacao", "color": "#ff4d4f"},
        {"id": 6, "name": "ponto_delta", "color": "#fadb14"},
        {"id": 7, "name": "nucleo_core", "color": "#eb2f96"},
        {"id": 8, "name": "documento_registro", "color": "#722ed1"}
    ]
}

ALL_DEFAULT_PRESETS = [
    PRESET_NAUTICAL,
    PRESET_ENVIRONMENT_SEGMENTATION,
    PRESET_PORT_SECURITY_PEOPLE,
    PRESET_PORT_INFRASTRUCTURE,
    PRESET_URBAN_TRAFFIC,
    PRESET_INDOOR_OFFICE,
    PRESET_NATURE_WILDLIFE,
    PRESET_OBJECTS_INDUSTRY,
    PRESET_TATTOO_STUDIO,
    PRESET_FINGERPRINTS_FORENSICS
]


class ClassPresetManager:
    """Gerencia e persiste conjuntos de classes de anotação para múltiplos domínios."""

    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.presets_dir = os.path.join(project_dir, "datasets", "class_presets")
        os.makedirs(self.presets_dir, exist_ok=True)
        self._init_default_presets()

    def _init_default_presets(self):
        """Inicializa os presets padrões se ainda não existirem."""
        for preset in ALL_DEFAULT_PRESETS:
            fpath = os.path.join(self.presets_dir, f"{preset['id']}.json")
            if not os.path.exists(fpath):
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(preset, f, indent=2, ensure_ascii=False)

    def list_presets(self, domain_filter=None):
        """Retorna todos os conjuntos de classes cadastrados, opcionalmente filtrados por domínio."""
        presets = []
        if os.path.exists(self.presets_dir):
            for f in os.listdir(self.presets_dir):
                if f.endswith(".json"):
                    fpath = os.path.join(self.presets_dir, f)
                    try:
                        with open(fpath, "r", encoding="utf-8") as fp:
                            data = json.load(fp)
                            if domain_filter is None or data.get("domain") == domain_filter:
                                presets.append(data)
                    except Exception:
                        pass
        return presets

    def get_preset(self, preset_id):
        """Obtém um conjunto de classes pelo seu ID."""
        for p in self.list_presets():
            if p.get("id") == preset_id:
                return p
        return PRESET_NAUTICAL

    def get_default_preset_for_domain(self, domain_id):
        """Retorna o preset padrão recomendado para o domínio especificado."""
        domain_map = {
            "naval": PRESET_NAUTICAL,
            "urbano": PRESET_URBAN_TRAFFIC,
            "fechado": PRESET_INDOOR_OFFICE,
            "natureza": PRESET_NATURE_WILDLIFE,
            "objetos": PRESET_OBJECTS_INDUSTRY,
            "tatuagens": PRESET_TATTOO_STUDIO,
            "digitais": PRESET_FINGERPRINTS_FORENSICS
        }
        return domain_map.get(domain_id, PRESET_NAUTICAL)

    def save_preset(self, preset_data):
        """Salva ou atualiza um conjunto de classes personalizado."""
        pid = preset_data.get("id") or f"classes_{int(time.time())}"
        preset_data["id"] = pid
        preset_data["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # Garante IDs numéricos sequenciais nas classes
        classes = preset_data.get("classes", [])
        for idx, c in enumerate(classes):
            c["id"] = idx
            if "color" not in c:
                colors = ["#00f0ff", "#1890ff", "#fa8c16", "#52c41a", "#722ed1", "#eb2f96", "#fadb14", "#ff4d4f", "#13c2c2"]
                c["color"] = colors[idx % len(colors)]
        preset_data["classes"] = classes

        fpath = os.path.join(self.presets_dir, f"{pid}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(preset_data, f, indent=2, ensure_ascii=False)
        return preset_data
