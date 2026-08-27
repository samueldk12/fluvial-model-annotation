"""
Script para Gerar Configuracoes de Treino YOLO dos Datasets do Roboflow Universe
Gera os arquivos data.yaml com as classes mapeadas de cada dataset do Roboflow Universe.
"""

import os
import yaml
import zipfile

def main():
    configs_dir = 'datasets/roboflow_naval/configs'
    os.makedirs(configs_dir, exist_ok=True)
    
    configs = {
        'coruna_ship_type.yaml': {
            'description': 'Ship-Type-Detection (University of Coruna - 12 Classes)',
            'names': {
                0: 'Aircraft Carrier', 1: 'Bulk Carrier', 2: 'Container Ship', 3: 'Cruise Ship',
                4: 'Drilling Ship', 5: 'LNG Tanker', 6: 'Naval Vessel', 7: 'Offshore Platform',
                8: 'Ro-Ro Ship', 9: 'Tanker', 10: 'Tug-Boat', 11: 'Yacht'
            }
        },
        'drone_aerial_boats.yaml': {
            'description': 'AerialViewFromDrones (UAV/Drone Maritime Perception)',
            'names': {
                0: 'Boat', 1: 'Ship', 2: 'Watercraft', 3: 'Buoy', 4: 'Obstacle', 5: 'Dock'
            }
        },
        'nir_infrared_ships.yaml': {
            'description': 'NIR Near-Infrared Maritime Vessel Detection',
            'names': {
                0: 'Ship', 1: 'Boat', 2: 'Vessel', 3: 'Barge'
            }
        },
        'maritime_surveillance.yaml': {
            'description': 'AI for Maritime Surveillance (Coastal Security)',
            'names': {
                0: 'Merchant Ship', 1: 'Cargo', 2: 'Fishing Boat', 3: 'Patrol Craft', 4: 'Speedboat', 5: 'Buoy'
            }
        },
        'ship_classification_pro.yaml': {
            'description': 'Ship Classification Pro (Harshas Workspace)',
            'names': {
                0: 'Container', 1: 'Tanker', 2: 'Bulk', 3: 'Passenger', 4: 'Naval'
            }
        },
        'naval_targets.yaml': {
            'description': 'Görüntü İşleme (Naval and Military Combat Targets)',
            'names': {
                0: 'Warship', 1: 'Frigate', 2: 'Corvette', 3: 'Submarine', 4: 'Patrol Boat'
            }
        }
    }
    
    for filename, cfg_data in configs.items():
        full_cfg = {
            'path': 'datasets/roboflow_naval/data_placeholder',
            'train': 'train/images',
            'val': 'valid/images',
            'test': 'test/images',
            'nc': len(cfg_data['names']),
            'names': cfg_data['names'],
            'roboflow_note': cfg_data['description']
        }
        file_path = os.path.join(configs_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(full_cfg, f, sort_keys=False)
        print(f"[OK] Gerado: {file_path} ({len(cfg_data['names'])} classes)")
        
    # Comprimir os arquivos de configuracao em datasets/archives/roboflow_naval_configs.zip
    archives_dir = 'datasets/archives'
    os.makedirs(archives_dir, exist_ok=True)
    zip_path = os.path.join(archives_dir, 'roboflow_naval_configs.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in os.listdir(configs_dir):
            fp = os.path.join(configs_dir, f)
            zf.write(fp, f)
        zf.write('datasets/roboflow_naval/roboflow_manifest.json', 'roboflow_manifest.json')
    print(f"\n[OK] Arquivo comprimido gerado: {zip_path} ({os.path.getsize(zip_path)/1024:.2f} KB)")

if __name__ == '__main__':
    main()
