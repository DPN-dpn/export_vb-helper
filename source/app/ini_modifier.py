import os
import shutil
import re
import uuid


def _copy_mod_folder(mod_folder_path, output_root, logger):
    """1단계: 원본 모드파일을 output 폴더로 복사"""
    logger.log("[1단계] 원본 모드파일을 output 폴더로 복사 중...")
    if not os.path.exists(output_root):
        os.makedirs(output_root)
    
    mod_folder_name = os.path.basename(os.path.normpath(mod_folder_path))
    output_mod_path = os.path.join(output_root, mod_folder_name)
    
    if os.path.exists(output_mod_path):
        shutil.rmtree(output_mod_path)
    
    shutil.copytree(mod_folder_path, output_mod_path)
    logger.log(f"모드 폴더 복사 완료: {output_mod_path}")
    
    return output_mod_path


def _collect_matched_pairs(asset_folder_path, component_slot_panel, logger):
    """2단계: 매칭된 파일 수집"""
    logger.log("[2단계] 매칭된 파일 수집 중...")
    component_values = component_slot_panel.get_component_values()
    components = component_slot_panel.controller.matcher.components
    
    asset_name = os.path.basename(os.path.normpath(asset_folder_path))
    matched_pairs = []
    
    for comp_idx, comp_widget in enumerate(component_values):
        comp = components[comp_idx]
        comp_name = comp["name"]
        
        # shared 슬롯 처리
        for key, var in comp_widget.get("shared", {}).items():
            value = var.get()
            if value:
                slot_name = f"{asset_name}{comp_name}{key}"
                matched_pairs.append((slot_name, value))
        
        # variant 슬롯 처리
        for variant_name, variant_widgets in comp_widget.get("variants", {}).items():
            for key, var in variant_widgets.items():
                value = var.get()
                if value:
                    if key.lower() == "ib":
                        if variant_name:
                            slot_name = f"{asset_name}{comp_name}{variant_name}"
                        else:
                            slot_name = f"{asset_name}{comp_name}"
                    else:
                        if variant_name:
                            slot_name = f"{asset_name}{comp_name}{variant_name}{key}"
                        else:
                            slot_name = f"{asset_name}{comp_name}{key}"
                    matched_pairs.append((slot_name, value))
    
    logger.log(f"매칭된 파일 수: {len(matched_pairs)}개")
    return matched_pairs


def _move_files_to_top(output_mod_path, matched_pairs, logger):
    """2-1단계: 매칭된 파일들과 ini 파일들을 최상위 폴더로 이동"""
    logger.log("[2-1단계] 매칭된 파일과 ini 파일을 최상위 폴더로 이동 중...")
    
    # ini 파일 찾기
    ini_files = []
    for root, dirs, files in os.walk(output_mod_path):
        for file in files:
            if file.lower().endswith('.ini'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, output_mod_path)
                ini_files.append(rel_path)
    
    # 원본 경로 저장
    original_paths = [matched_file for _, matched_file in matched_pairs]
    
    # 매칭된 파일 이동
    for idx, (slot_name, matched_file) in enumerate(matched_pairs):
        src_path = os.path.join(output_mod_path, matched_file)
        if os.path.exists(src_path) and ('/' in matched_file or '\\' in matched_file):
            filename = os.path.basename(matched_file)
            dst_path = os.path.join(output_mod_path, filename)
            
            counter = 1
            base_name, ext = os.path.splitext(filename)
            while os.path.exists(dst_path):
                filename = f"{base_name}_{counter}{ext}"
                dst_path = os.path.join(output_mod_path, filename)
                counter += 1
            
            shutil.move(src_path, dst_path)
            matched_pairs[idx] = (slot_name, filename)
            logger.log(f"이동: {matched_file} -> {filename}")
        else:
            moved_filename = os.path.basename(matched_file)
            matched_pairs[idx] = (slot_name, moved_filename)
    
    # ini 파일 이동
    for idx, ini_file in enumerate(ini_files):
        src_path = os.path.join(output_mod_path, ini_file)
        if '/' in ini_file or '\\' in ini_file:
            filename = os.path.basename(ini_file)
            dst_path = os.path.join(output_mod_path, filename)
            
            counter = 1
            base_name, ext = os.path.splitext(filename)
            while os.path.exists(dst_path):
                filename = f"{base_name}_{counter}{ext}"
                dst_path = os.path.join(output_mod_path, filename)
                counter += 1
            
            shutil.move(src_path, dst_path)
            ini_files[idx] = filename
            logger.log(f"이동: {ini_file} -> {filename}")
        else:
            ini_files[idx] = ini_file
    
    return matched_pairs, ini_files, original_paths


def _update_ini_file_paths(output_mod_path, ini_files, matched_pairs, original_paths, logger):
    """2-2단계: ini 파일의 filename = 경로 수정"""
    logger.log("[2-2단계] ini 파일의 경로 수정 중...")
    
    for new_ini_filename in ini_files:
        ini_path = os.path.join(output_mod_path, new_ini_filename)
        
        with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
            ini_content = f.read()
        
        for idx, original_path in enumerate(original_paths):
            new_filename = matched_pairs[idx][1]
            
            patterns = [
                original_path,
                original_path.replace('/', '\\'),
                original_path.replace('\\', '/'),
            ]
            
            for pattern in patterns:
                # replacement 문자열에서 '\1'과 파일명 바로 뒤에 숫자가 올 경우
                # '\18' 같은 잘못된 그룹 참조로 해석되는 문제가 있어,
                # 서브 함수로 처리하여 그룹을 안전하게 결합한다.
                pat = re.compile(r'(filename\s*=\s*)(%s)' % re.escape(pattern), flags=re.IGNORECASE)
                ini_content = pat.sub(lambda m, nf=new_filename: m.group(1) + nf, ini_content)
        
        with open(ini_path, 'w', encoding='utf-8') as f:
            f.write(ini_content)
        
        logger.log(f"ini 파일 경로 수정 완료: {new_ini_filename}")


def _rename_to_temp_files(output_mod_path, matched_pairs, logger):
    """3-1단계: 매칭할 파일명을 임시 문자열로 변경"""
    logger.log("[3-1단계] 파일명을 임시 문자열로 변경 중...")
    
    # ini 수정을 위해 이동 후 파일명 저장
    moved_filenames = [moved_filename for _, moved_filename in matched_pairs]
    
    for idx, (slot_name, moved_filename) in enumerate(matched_pairs):
        old_path = os.path.join(output_mod_path, moved_filename)
        if os.path.exists(old_path):
            temp_filename = f"TEMP_{uuid.uuid4().hex}{os.path.splitext(moved_filename)[1]}"
            temp_path = os.path.join(output_mod_path, temp_filename)
            
            os.rename(old_path, temp_path)
            # matched_pairs 업데이트
            matched_pairs[idx] = (slot_name, temp_filename)
            logger.log(f"임시 변경: {moved_filename} -> {temp_filename}")
    
    return matched_pairs, moved_filenames


def _rename_to_final_files(output_mod_path, matched_pairs, logger):
    """3-2단계: 임시 문자열을 최종 매칭된 파일명으로 변경"""
    logger.log("[3-2단계] 임시 파일명을 최종 파일명으로 변경 중...")
    
    for idx, (slot_name, temp_filename) in enumerate(matched_pairs):
        ext = os.path.splitext(temp_filename)[1]
        final_filename = f"{slot_name}{ext}"
        
        temp_path = os.path.join(output_mod_path, temp_filename)
        final_path = os.path.join(output_mod_path, final_filename)
        
        counter = 1
        base_name, ext = os.path.splitext(final_filename)
        while os.path.exists(final_path):
            final_filename = f"{base_name}_{counter}{ext}"
            final_path = os.path.join(output_mod_path, final_filename)
            counter += 1
        
        os.rename(temp_path, final_path)
        # matched_pairs 업데이트
        matched_pairs[idx] = (slot_name, final_filename)
        logger.log(f"최종 변경: {temp_filename} -> {final_filename}")
    
    return matched_pairs


def _update_ini_file_contents(output_mod_path, ini_files, matched_pairs, moved_filenames, logger):
    """4단계: ini 파일 내용 변경"""
    logger.log("[4단계] ini 파일 내용 변경 중...")
    
    for new_ini_filename in ini_files:
        ini_path = os.path.join(output_mod_path, new_ini_filename)
        
        logger.log(f"  처리 중: {new_ini_filename}")
        with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
            ini_content = f.read()
        
        # 4-1단계: 이동 후 파일명 -> 임시 문자열로 교체
        temp_strings = {}
        for idx, (slot_name, final_filename) in enumerate(matched_pairs):
            moved_filename = moved_filenames[idx]
            moved_name_no_ext = os.path.splitext(moved_filename)[0]
            final_name_no_ext = os.path.splitext(final_filename)[0]
            
            temp_str = f"TEMP_INI_{uuid.uuid4().hex}"
            temp_strings[temp_str] = final_name_no_ext
            
            logger.log(f"    임시 교체: {moved_name_no_ext} -> {temp_str}")
            ini_content = ini_content.replace(moved_name_no_ext, temp_str)
        
        # 4-2단계: 임시 문자열 -> 최종 파일명으로 교체
        for temp_str, final_name_no_ext in temp_strings.items():
            logger.log(f"    최종 교체: {temp_str} -> {final_name_no_ext}")
            ini_content = ini_content.replace(temp_str, final_name_no_ext)
        
        # 4-3단계: 특정 구문 삭제
        logger.log(f"  4-3단계: 특정 구문 삭제 중...")
        
        # 4-3-1단계: Resource로 시작하고 CS로 끝나는 섹션 삭제 (붕스 대응)
        ini_content = _remove_resource_cs_sections(ini_content, logger)
        
        # 4-3-2단계: Resource로 시작하는데 filename=이 없는 섹션 삭제 및 참조 제거 (copy vb 대응)
        ini_content = _remove_resource_sections_without_filename(ini_content, logger)
        
        # 4-3-3단계: Resource로 시작하고 format=이 있지만 filename 확장자가 .ib가 아닌 섹션 삭제 및 참조 제거
        ini_content = _remove_resource_sections_fake_ib_file(ini_content, logger)
        
        # 4-4단계: 특정 구문 처리
        logger.log(f"  4-3단계: 특정 구문 처리 중...")
        
        # 4-4-1단계: != 조건문을 (A > B || A < B) 형태로 교체
        ini_content = _replace_not_equal_conditions(ini_content, logger)
        
        with open(ini_path, 'w', encoding='utf-8') as f:
            f.write(ini_content)
        
        logger.log(f"  완료: {new_ini_filename}")


def _remove_resource_cs_sections(ini_content, logger):
    """4-3-1단계: Resource로 시작하고 CS로 끝나는 섹션 삭제"""
    sections_to_remove = []
    lines = ini_content.split('\n')
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if line_stripped.startswith('[') and line_stripped.endswith(']'):
            section_name = line_stripped[1:-1].strip()
            if section_name.startswith('Resource') and section_name.endswith('CS'):
                sections_to_remove.append(section_name)
                logger.log(f"    삭제할 섹션 발견: {section_name}")
    
    # 섹션 삭제
    for section_name in sections_to_remove:
        pattern = rf'\[{re.escape(section_name)}\].*?(?=\n\[|\Z)'
        ini_content = re.sub(pattern, '', ini_content, flags=re.DOTALL)
    
    return ini_content


def _replace_not_equal_conditions(ini_content, logger):
    """4-4단계: != 조건문을 (A > B || A < B) 형태로 교체"""
    # A != B 패턴 찾기 (양쪽에 공백이 있을 수 있음)
    # 패턴: 단어/숫자/변수 != 단어/숫자/변수
    pattern = r'(\S+)\s*!=\s*(\S+)'
    
    def replace_func(match):
        left = match.group(1)
        right = match.group(2)
        replacement = f"({left} > {right} || {left} < {right})"
        logger.log(f"    교체: {match.group(0)} -> {replacement}")
        return replacement
    
    original_content = ini_content
    ini_content = re.sub(pattern, replace_func, ini_content)
    
    replaced_count = len(re.findall(pattern, original_content))
    if replaced_count > 0:
        logger.log(f"    != 조건문 {replaced_count}개 교체 완료")
    
    return ini_content


def _remove_resource_sections_without_filename(ini_content, logger):
    """4-3-2단계: Resource로 시작하는데 filename=이 없는 섹션 삭제 및 참조 제거"""
    sections_to_remove = []
    lines = ini_content.split('\n')
    
    i = 0
    while i < len(lines):
        line_stripped = lines[i].strip()
        
        # 섹션 시작 찾기
        if line_stripped.startswith('[') and line_stripped.endswith(']'):
            section_name = line_stripped[1:-1].strip()
            
            if section_name.startswith('Resource'):
                # 다음 섹션까지 확인
                j = i + 1
                has_filename = False
                
                while j < len(lines):
                    next_line = lines[j].strip()
                    
                    # 다음 섹션 시작
                    if next_line.startswith('[') and next_line.endswith(']'):
                        break
                    
                    # filename= 구문 확인
                    if next_line.lower().startswith('filename'):
                        has_filename = True
                        break
                    
                    j += 1
                
                if not has_filename:
                    sections_to_remove.append(section_name)
                    logger.log(f"    filename 없는 섹션 발견: {section_name}")
        
        i += 1
    
    # 섹션 삭제
    for section_name in sections_to_remove:
        pattern = rf'\[{re.escape(section_name)}\].*?(?=\n\[|\Z)'
        ini_content = re.sub(pattern, '', ini_content, flags=re.DOTALL)
    
    # 참조 제거 (해당 섹션 이름을 포함하는 줄 삭제)
    for section_name in sections_to_remove:
        lines = ini_content.split('\n')
        filtered_lines = []
        
        for line in lines:
            # 섹션 헤더가 아니면서 섹션 이름을 포함하는 줄 제거
            line_stripped = line.strip()
            if not (line_stripped.startswith('[') and line_stripped.endswith(']')):
                if section_name in line:
                    logger.log(f"    참조 제거: {line.strip()}")
                    continue
            
            filtered_lines.append(line)
        
        ini_content = '\n'.join(filtered_lines)
    
    return ini_content


def _remove_resource_sections_fake_ib_file(ini_content, logger):
    """4-3-3단계: Resource로 시작하고 format=이 있지만 filename=의 확장자가 .ib가 아닌 섹션 삭제"""
    lines = ini_content.split('\n')
    to_remove_ranges = []  # list of (start_idx, end_idx)
    sections_to_remove = []

    i = 0
    while i < len(lines):
        line_stripped = lines[i].strip()
        if line_stripped.startswith('[') and line_stripped.endswith(']'):
            section_name = line_stripped[1:-1].strip()
            if section_name.startswith('Resource'):
                # find next section start
                j = i + 1
                has_format = False
                filename_value = None

                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line.startswith('[') and next_line.endswith(']'):
                        break

                    # check format=
                    if re.match(r'(?i)format\s*=\s*', next_line):
                        has_format = True

                    # check filename=
                    m = re.match(r'(?i)filename\s*=\s*(.*)', next_line)
                    if m:
                        val = m.group(1).strip()
                        # remove surrounding quotes if any
                        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                            val = val[1:-1]
                        filename_value = val
                        # keep scanning to get format presence too

                    j += 1

                # if format exists and filename present but ext != .ib -> remove
                if has_format and filename_value:
                    _, ext = os.path.splitext(filename_value)
                    if ext.lower() != '.ib':
                        to_remove_ranges.append((i, j))
                        sections_to_remove.append(section_name)
                        logger.log(f"    format 있으나 .ib 아님으로 삭제 대상: {section_name} (filename={filename_value})")

                i = j
                continue

        i += 1

    if not to_remove_ranges:
        return ini_content

    # remove section ranges
    remove_idx = set()
    for start, end in to_remove_ranges:
        for k in range(start, end):
            remove_idx.add(k)

    filtered_lines = [ln for idx, ln in enumerate(lines) if idx not in remove_idx]

    ini_content = '\n'.join(filtered_lines)

    # 참조 제거 (해당 섹션 이름을 포함하는 줄 삭제, 섹션 헤더는 이미 제거됨)
    if sections_to_remove:
        lines = ini_content.split('\n')
        final_lines = []
        for line in lines:
            line_stripped = line.strip()
            # 섹션 헤더가 아니고, 섹션 이름을 포함하면 제거
            if not (line_stripped.startswith('[') and line_stripped.endswith(']')):
                skip = False
                for sec in sections_to_remove:
                    if sec in line:
                        logger.log(f"    참조 제거: {line_stripped}")
                        skip = True
                        break
                if skip:
                    continue
            final_lines.append(line)

        ini_content = '\n'.join(final_lines)

    return ini_content


def generate_ini(
    asset_folder_path,
    mod_folder_path,
    component_slot_panel,
    output_root="output",
    logger=None,
):
    """
    모드 파일과 매칭 정보를 바탕으로 최종 ini 파일을 생성합니다.
    
    단계:
    1. 원본 모드파일을 output폴더로 전부 복사
    2. 매칭된 파일 수집하기
    2-1. 복사한 모드폴더에서 매칭된 파일들과 ini파일들이 모드 내 폴더 경로에 있을 때 최상폴더로 꺼냄
    2-2. ini의 filename = 에서 변경된 경로로 수정
    3. 파일명 변경
    3-1. 매칭할 파일명들을 임시 문자열로 변경
    3-2. 임시 문자열들을 제대로 매칭된 파일명으로 변경
    4. ini 변경
    4-1. 매칭한 문자열을 임시 문자열로 변경
    4-2. 임시 문자열을 매칭된 문자열로 변경
    4-3. 특정 구문 삭제
    4-4. 특정 구문 처리
    5. 완료
    """
    
    # 1단계: 원본 모드파일을 output 폴더로 복사
    output_mod_path = _copy_mod_folder(mod_folder_path, output_root, logger)
    
    # 2단계: 매칭된 파일 수집
    matched_pairs = _collect_matched_pairs(asset_folder_path, component_slot_panel, logger)
    
    # 2-1단계: 파일들을 최상위 폴더로 이동
    matched_pairs, ini_files, original_paths = _move_files_to_top(output_mod_path, matched_pairs, logger)
    
    # 2-2단계: ini 파일의 filename = 경로 수정
    _update_ini_file_paths(output_mod_path, ini_files, matched_pairs, original_paths, logger)
    
    # 3단계: 파일명 변경
    logger.log("[3단계] 파일명 변경 중...")
    
    # 3-1단계: 임시 파일명으로 변경
    matched_pairs, moved_filenames = _rename_to_temp_files(output_mod_path, matched_pairs, logger)
    
    # 3-2단계: 최종 파일명으로 변경
    matched_pairs = _rename_to_final_files(output_mod_path, matched_pairs, logger)
    
    # 4단계: ini 파일 내용 변경
    logger.log("[4단계] ini 파일 내용 변경 중...")
    _update_ini_file_contents(output_mod_path, ini_files, matched_pairs, moved_filenames, logger)
    
    # 5단계: 완료
    logger.log("[5단계] 완료!")
    logger.log(f"출력 경로: {output_mod_path}")
    logger.log(f"처리된 파일 수: {len(matched_pairs)}개")
    
    return output_mod_path
