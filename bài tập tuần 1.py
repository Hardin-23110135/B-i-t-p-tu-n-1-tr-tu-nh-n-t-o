# -*- coding: utf-8 -*-

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple


# Cấu hình UTF-8 cho Windows khi có thể
if hasattr(sys.stdout, "reconfigure"):
	sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
	sys.stderr.reconfigure(encoding="utf-8")


@dataclass
class OptionScore:
	name: str
	score: float
	reasons: List[str]
	feasible: bool = True


def ask_yes_no(prompt: str) -> bool:
	while True:
		answer = input(f"{prompt} (yes/no): ").strip().lower()
		if answer in ("y", "yes", "có", "co", "1"):
			return True
		if answer in ("n", "no", "không", "khong", "0"):
			return False
		print("Vui lòng nhập 'yes' hoặc 'no'.")


def ask_float(prompt: str, min_value: float | None = None, max_value: float | None = None) -> float:
	while True:
		raw = input(f"{prompt}: ").strip().replace(",", ".")
		try:
			value = float(raw)
			if min_value is not None and value < min_value:
				print(f"Giá trị phải ≥ {min_value}.")
				continue
			if max_value is not None and value > max_value:
				print(f"Giá trị phải ≤ {max_value}.")
				continue
			return value
		except ValueError:
			print("Vui lòng nhập số hợp lệ.")


def ask_choice(prompt: str, choices: List[str]) -> str:
	choices_str = ", ".join(choices)
	while True:
		answer = input(f"{prompt} ({choices_str}): ").strip().lower()
		if answer in choices:
			return answer
		print("Vui lòng chọn một trong các lựa chọn đã liệt kê.")


def estimate_minutes_for_distance(distance_km: float, speed_kmh: float) -> float:
	if speed_kmh <= 0:
		return math.inf
	return distance_km / speed_kmh * 60.0


def evaluate_transport_options(facts: Dict) -> List[OptionScore]:
	options: Dict[str, OptionScore] = {
		"Đi bộ": OptionScore("Đi bộ", 0.0, []),
		"Đạp xe": OptionScore("Đạp xe", 0.0, []),
		"Xe buýt": OptionScore("Xe buýt", 0.0, []),
		"Nhờ người thân đưa đón": OptionScore("Nhờ người thân đưa đón", 0.0, []),
	}

	distance_km = facts["distance_km"]
	weather = facts["weather"]
	time_left_min = facts["time_left_min"]
	energy = facts["energy"]
	has_bike = facts["has_bike"]
	bike_ok = facts["bike_ok"]
	has_helmet = facts["has_helmet"]
	has_rain_gear = facts["has_rain_gear"]
	bus_available = facts["bus_available"]
	bus_can_pay = facts["bus_can_pay"]
	bus_wait_min = facts["bus_wait_min"] if bus_available else 0
	guardian_available = facts["guardian_available"]

	# Ràng buộc khả dụng
	if not has_bike:
		options["Đạp xe"].feasible = False
		options["Đạp xe"].reasons.append("Không có xe đạp sẵn dùng.")
	if has_bike and not bike_ok:
		options["Đạp xe"].feasible = False
		options["Đạp xe"].reasons.append("Xe đạp không đảm bảo tình trạng tốt.")
	if has_bike and not has_helmet:
		# Không hủy khả dụng, nhưng phạt rất nặng vì an toàn
		options["Đạp xe"].score -= 5
		options["Đạp xe"].reasons.append("Thiếu mũ bảo hiểm: giảm điểm an toàn.")
	if not bus_available or not bus_can_pay:
		if not bus_available:
			options["Xe buýt"].feasible = False
			options["Xe buýt"].reasons.append("Khu vực/khung giờ không có xe buýt phù hợp.")
		if bus_available and not bus_can_pay:
			options["Xe buýt"].feasible = False
			options["Xe buýt"].reasons.append("Không có vé/thẻ/chi phí đi xe buýt.")
	if not guardian_available:
		options["Nhờ người thân đưa đón"].feasible = False
		options["Nhờ người thân đưa đón"].reasons.append("Không có người thân rảnh để đưa đón.")

	# 1) Quãng đường
	if distance_km <= 0.8:
		options["Đi bộ"].score += 3; options["Đi bộ"].reasons.append("Quãng đường rất gần, phù hợp đi bộ.")
	elif distance_km <= 1.5:
		options["Đi bộ"].score += 1; options["Đi bộ"].reasons.append("Quãng đường gần, có thể đi bộ.")
	elif distance_km > 2.0:
		options["Đi bộ"].score -= 3; options["Đi bộ"].reasons.append("Quãng đường xa, đi bộ sẽ mất nhiều thời gian.")

	if distance_km <= 1.0:
		options["Đạp xe"].score += 1; options["Đạp xe"].reasons.append("Quãng đường gần, đạp xe nhanh gọn.")
	elif distance_km <= 5.0:
		options["Đạp xe"].score += 3; options["Đạp xe"].reasons.append("Quãng đường trung bình, đạp xe là lựa chọn tốt.")
	elif distance_km > 7.0:
		options["Đạp xe"].score -= 2; options["Đạp xe"].reasons.append("Quãng đường khá xa để đạp xe thoải mái.")

	if distance_km > 3.0:
		options["Xe buýt"].score += 3; options["Xe buýt"].reasons.append("Quãng đường xa, xe buýt thuận tiện.")
	elif distance_km <= 1.0:
		options["Xe buýt"].score -= 2; options["Xe buýt"].reasons.append("Quãng đường rất gần, xe buýt kém linh hoạt.")

	if distance_km > 2.0:
		options["Nhờ người thân đưa đón"].score += 2; options["Nhờ người thân đưa đón"].reasons.append("Quãng đường xa, nhờ đưa đón đỡ mệt và nhanh hơn.")

	# 2) Thời tiết
	if weather == "khô ráo":
		options["Đi bộ"].score += 1; options["Đi bộ"].reasons.append("Thời tiết khô ráo, đi bộ dễ chịu.")
		options["Đạp xe"].score += 1; options["Đạp xe"].reasons.append("Thời tiết khô ráo, đạp xe thoải mái.")
	elif weather == "mưa nhẹ":
		options["Đi bộ"].score -= 1; options["Đi bộ"].reasons.append("Mưa nhẹ, đi bộ có thể bất tiện.")
		if has_rain_gear:
			options["Đạp xe"].score += 0; options["Đạp xe"].reasons.append("Có áo mưa/ô, vẫn có thể đạp xe.")
		else:
			options["Đạp xe"].score -= 2; options["Đạp xe"].reasons.append("Mưa nhẹ và không có áo mưa/ô.")
		options["Xe buýt"].score += 1; options["Xe buýt"].reasons.append("Mưa nhẹ, đi xe buýt kín mưa.")
	elif weather in ("mưa to", "gió mạnh"):
		options["Đi bộ"].score -= 3; options["Đi bộ"].reasons.append("Thời tiết xấu, đi bộ không thoải mái.")
		if has_rain_gear:
			options["Đạp xe"].score -= 1; options["Đạp xe"].reasons.append("Thời tiết xấu dù có áo mưa, đạp xe vẫn rủi ro.")
		else:
			options["Đạp xe"].score -= 4; options["Đạp xe"].reasons.append("Thời tiết xấu và không có áo mưa: không nên đạp xe.")
		options["Xe buýt"].score += 3; options["Xe buýt"].reasons.append("Thời tiết xấu, xe buýt an toàn và khô ráo hơn.")
		options["Nhờ người thân đưa đón"].score += 2; options["Nhờ người thân đưa đón"].reasons.append("Thời tiết xấu, nhờ đưa đón an toàn hơn.")
	elif weather == "nắng gắt":
		options["Đi bộ"].score -= 1; options["Đi bộ"].reasons.append("Nắng gắt, đi bộ dễ mệt.")
		options["Đạp xe"].score -= 1; options["Đạp xe"].reasons.append("Nắng gắt, đạp xe có thể mệt.")
		options["Xe buýt"].score += 1; options["Xe buýt"].reasons.append("Nắng gắt, xe buýt mát hơn.")

	# 3) Thời gian còn lại so với thời gian ước tính di chuyển
	walk_eta = estimate_minutes_for_distance(distance_km, 4.5)
	bike_eta = estimate_minutes_for_distance(distance_km, 12.0)
	bus_eta = bus_wait_min + estimate_minutes_for_distance(distance_km, 20.0)
	car_eta = estimate_minutes_for_distance(distance_km, 25.0)

	def apply_eta(option_key: str, eta_min: float, buffer_min: float) -> None:
		if eta_min + buffer_min > time_left_min:
			options[option_key].score -= 5
			options[option_key].reasons.append(
				f"Không kịp giờ: cần ~{eta_min:.0f} phút + đệm {buffer_min:.0f} phút, còn {time_left_min:.0f} phút."
			)
		else:
			options[option_key].score += 2
			options[option_key].reasons.append(
				f"Kịp giờ: cần ~{eta_min:.0f} phút + đệm {buffer_min:.0f} phút, còn {time_left_min:.0f} phút."
			)

	apply_eta("Đi bộ", walk_eta, 5)
	apply_eta("Đạp xe", bike_eta, 5)
	apply_eta("Xe buýt", bus_eta, 10)
	apply_eta("Nhờ người thân đưa đón", car_eta, 5)

	# 4) Thể trạng/ năng lượng
	if energy == "thấp":
		options["Đi bộ"].score -= 3; options["Đi bộ"].reasons.append("Thể trạng thấp, đi bộ dễ mệt.")
		options["Đạp xe"].score -= 2; options["Đạp xe"].reasons.append("Thể trạng thấp, đạp xe không phù hợp.")
		options["Xe buýt"].score += 2; options["Xe buýt"].reasons.append("Thể trạng thấp, xe buýt đỡ tốn sức.")
		options["Nhờ người thân đưa đón"].score += 2; options["Nhờ người thân đưa đón"].reasons.append("Thể trạng thấp, nhờ đưa đón đỡ mệt.")
	elif energy == "cao":
		options["Đi bộ"].score += 1; options["Đi bộ"].reasons.append("Thể trạng tốt, đi bộ/đạp xe phù hợp.")
		options["Đạp xe"].score += 1; options["Đạp xe"].reasons.append("Thể trạng tốt, đạp xe phù hợp.")

	# Tổng hợp: hủy lựa chọn không khả dụng
	for key, opt in options.items():
		if not opt.feasible:
			opt.score = -math.inf

	# Xếp hạng
	ranked = sorted(options.values(), key=lambda o: o.score, reverse=True)
	return ranked


def print_recommendation(ranked: List[OptionScore]) -> None:
	best = ranked[0]
	if best.score == -math.inf:
		print("\nKhông có phương án khả thi dựa trên thông tin đã cung cấp. Hãy điều chỉnh điều kiện đầu vào.")
		return
	print("\n=== Khuyến nghị phương tiện ===")
	print(f"Nên chọn: {best.name}")
	print(f"Điểm tổng: {best.score:.1f}")
	print("\nLý do chính:")
	for reason in best.reasons[:8]:
		print(f"- {reason}")
	if len(best.reasons) > 8:
		print(f"- ... và {len(best.reasons) - 8} lý do bổ sung")

	print("\nXếp hạng đầy đủ:")
	for i, opt in enumerate(ranked, 1):
		status = "khả dụng" if opt.score > -math.inf else "không khả dụng"
		print(f"{i}. {opt.name}: {opt.score if math.isfinite(opt.score) else '-∞'} ({status})")


def main() -> None:
	print("Hệ chuyên gia: Gợi ý phương tiện đến trường")
	print("Trả lời vài câu hỏi ngắn để nhận khuyến nghị phù hợp.\n")

	distance_km = ask_float("1) Quãng đường từ nhà đến trường (km)", 0.1, 50)
	weather = ask_choice(
		"2) Thời tiết hiện tại",
		["khô ráo", "mưa nhẹ", "mưa to", "gió mạnh", "nắng gắt"],
	)
	has_rain_gear = ask_yes_no("3) Có áo mưa hoặc ô không")
	time_left_min = ask_float("4) Còn bao nhiêu phút nữa là đến giờ vào lớp", 1, 300)
	energy = ask_choice("5) Mức năng lượng hiện tại", ["thấp", "trung bình", "cao"])

	has_bike = ask_yes_no("6) Có xe đạp để sử dụng không")
	bike_ok = True
	has_helmet = True
	if has_bike:
		bike_ok = ask_yes_no("   - Xe đạp đang trong tình trạng tốt?")
		has_helmet = ask_yes_no("   - Có mũ bảo hiểm không")

	bus_available = ask_yes_no("7) Khu vực/khung giờ này có xe buýt phù hợp không")
	bus_can_pay = True
	bus_wait_min = 0.0
	if bus_available:
		bus_can_pay = ask_yes_no("   - Có vé/thẻ hoặc tiền đi xe buýt không")
		bus_wait_min = ask_float("   - Thời gian chờ xe buýt ước tính (phút)", 0, 60)

	guardian_available = ask_yes_no("8) Có người thân rảnh để đưa đón không")

	facts = {
		"distance_km": distance_km,
		"weather": weather,
		"time_left_min": time_left_min,
		"energy": energy,
		"has_bike": has_bike,
		"bike_ok": bike_ok,
		"has_helmet": has_helmet,
		"has_rain_gear": has_rain_gear,
		"bus_available": bus_available,
		"bus_can_pay": bus_can_pay,
		"bus_wait_min": bus_wait_min,
		"guardian_available": guardian_available,
	}

	ranked = evaluate_transport_options(facts)
	print_recommendation(ranked)


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print("\nĐã hủy theo yêu cầu người dùng.") 