with open("src/web/app.py", "r", encoding="utf-8") as f:
    text = f.read()

p1 = text.find("water_overlay = display_frame.copy()")
p2 = text.find("cv2.polylines(display_frame, [water_polygon], True, (0, 229, 255), 1)")
if p1 != -1 and p2 != -1:
    p2_end = text.find("\n", p2)
    text = text[:p1] + "        # Video Real 100% Limpo\n" + text[p2_end+1:]

b1 = text.find("hull_color = (0, 230, 118)")
b2 = text.find("current_live_vessels.append({")
if b1 != -1 and b2 != -1:
    clean_box = """               # 1. CONTORNO DO BARCO (Verde se parado, Ciano se navegando)
                hull_color = (0, 230, 118) if is_stationary else (0, 240, 255)
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), hull_color, 2)

                # 2. PREVISAO PARA ONDE VAI
                if is_stationary:
                    cv2.circle(display_frame, (int(cx), int(cy)), 3, (0, 230, 118), -1)
                else:
                    future_pts = spatial_memory.predict_future_positions(v_mem, [5.0, 10.0])
                    if len(future_pts) >= 2:
                        p5, p10 = future_pts[0], future_pts[1]
                        cv2.line(display_frame, (int(cx), int(cy)), (p10["x"], p10["y"]), (0, 255, 120), 2, cv2.LINE_AA)
                        cv2.circle(display_frame, (p10["x"], p10["y"]), 5, (0, 255, 120), -1)
                        dest_label = "-> " + dynamic_destination[:18]
                        cv2.putText(display_frame, dest_label, (p10["x"] + 6, p10["y"] + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 120), 1, cv2.LINE_AA)

                # 3. ETIQUETA NO VIDEO: APENAS ID E ESTADO
                status_short = "PARADO (0.0 nos)" if is_stationary else "NAVEGANDO (" + str(round(speed_val, 1)) + " px/s)"
                tag_str = v_id + " | " + status_short
                
                (tw, th), _ = cv2.getTextSize(tag_str, cv2.FONT_HERSHEY_SIMPLEX, 0.44, 1)
                tag_y = max(th + 8, y1 - 6)
                
                tag_bg = display_frame.copy()
                cv2.rectangle(tag_bg, (x1, tag_y - th - 5), (x1 + tw + 10, tag_y + 3), (6, 12, 18), -1)
                cv2.addWeighted(tag_bg, 0.85, display_frame, 0.15, 0, display_frame)
                cv2.rectangle(display_frame, (x1, tag_y - th - 5), (x1 + tw + 10, tag_y + 3), hull_color, 1)
                cv2.putText(display_frame, tag_str, (x1 + 5, tag_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)

                ens_pct = int(det.get("score_ensemble_final", 0.85) * 100)
                norm_pct = int(det.get("conf_normal", 0.0) * 100)
                night_pct = int(det.get("conf_night", 0.0) * 100)
                mem_pct = int(v_mem["memory_strength"] * 100)
                origin_text = v_mem.get("origin_story", "Entrou no canal as " + v_mem.get("first_registered", "--"))
"""
    text = text[:b1] + clean_box + text[b2:]

text = text.replace(
    '"fingerprint": fingerprint\n                }',
    '"fingerprint": fingerprint,\n                    "first_registered": v_mem.get("first_registered", "--"),\n                    "origin_story": origin_text\n                }'
)

with open("src/web/app.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Updated video stream overlay in app.py")
