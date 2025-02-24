import re
import subprocess
import tempfile
import os

def run_openssl(command, input_data=None, text_output=True):
    """เรียกใช้งาน OpenSSL และคืนค่าผลลัพธ์"""
    try:
        result = subprocess.run(
            command,
            input=input_data,
            capture_output=True,
            check=True,
            text=text_output
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("❌ OpenSSL Error:", e.stderr)
        return None

def extract_certificate_from_signature(signature_binary, output_cert_path):
    """ดึงใบรับรองจากลายเซ็น (PKCS#7) และบันทึกเป็น PEM"""
    with tempfile.NamedTemporaryFile(delete=False) as temp_sig_file:
        temp_sig_file.write(signature_binary)
        temp_sig_file_path = temp_sig_file.name
    
    command = ["openssl", "pkcs7", "-inform", "DER", "-print_certs", "-out", output_cert_path]
    result = run_openssl(command, signature_binary, text_output=False)
    os.remove(temp_sig_file_path)
    
    return os.path.exists(output_cert_path)

def verify_certificate(ca_cert_path, cert_path):
    """ตรวจสอบใบรับรองกับ CA ที่กำหนด"""
    command = ["openssl", "verify", "-CAfile", ca_cert_path, cert_path]
    result = run_openssl(command)
    return result and "OK" in result

def extract_certificates(pdf_path, ca_cert_path):
    """ดึงลายเซ็นจากไฟล์ PDF, ตรวจสอบ, และดึงชื่อผู้เซ็น"""
    try:
        with open(pdf_path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"❌ ไม่พบไฟล์ PDF: {pdf_path}")
        return []
    
    # ค้นหาลายเซ็นในไฟล์ PDF
    matches = re.findall(rb"/Contents<([0-9A-Fa-f]+)>", data)
    verified_signer_names = []
    
    for i, hex_data in enumerate(matches):
        signature_binary = bytes.fromhex(hex_data.decode())
        cert_path = f"cert_{i}.pem"
        
        # ดึงใบรับรองจากลายเซ็น
        if extract_certificate_from_signature(signature_binary, cert_path):
            # ตรวจสอบใบรับรองกับ CA
            if verify_certificate(ca_cert_path, cert_path):
                
                # ดึงข้อมูลลายเซ็นโดยตรง
                with tempfile.NamedTemporaryFile(delete=False) as temp_sig_file:
                    temp_sig_file.write(signature_binary)
                    temp_sig_file_path = temp_sig_file.name
            
                # ใช้ OpenSSL เพื่อตรวจสอบลายเซ็นและดึงข้อมูล
                output_text = run_openssl(["openssl", "pkcs7", "-inform", "DER", "-in", temp_sig_file_path, "-print_certs", "-noout", "-text"])
                
                # ลบไฟล์ชั่วคราวหลังจากใช้งานเสร็จ
                os.remove(temp_sig_file_path)
                
                if output_text:
                    cn_matches = re.findall(r"CN=([^,\n]+)", output_text)

                    verified_signer_names.append(cn_matches[-1].split('/')[0])
                else:
                    pass
    return verified_signer_names

# ตัวอย่างการใช้งาน
# cert_path = 'trurt_cert.pem'  # ไฟล์ CA ของคุณ
# pdf_path = 'your_pdf.pdf'  # ไฟล์ PDF ของคุณ
# verified_signers = extract_certificates(pdf_path, cert_path)
# print("ชื่อผู้เซ็นที่ผ่านการตรวจสอบ:", verified_signers)