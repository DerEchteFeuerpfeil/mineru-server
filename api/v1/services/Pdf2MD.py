import logging
import os
import subprocess

import torch

log = logging.getLogger("__main__." + __name__)


def remove_extension(filename):
    return os.path.splitext(filename)[0]


def processPdf2MD(input_path:str, output_path:str):
    """
    NOTE: Currently this function is hard-coded for German texts
    """
    cmd = ["magic-pdf", "-p", input_path, "-o", output_path, "-m", "ocr", "-l", "german"]
    try:
        log.info(f"Running command: {cmd}")

        # Start the process and log output in real-time
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Log output line by line
        for stdout_line in iter(process.stdout.readline, ""):
            log.info(stdout_line.strip())

        for stderr_line in iter(process.stderr.readline, ""):
            log.warning(stderr_line.strip())

        process.stdout.close()
        process.stderr.close()

        return_code = process.wait()

        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, cmd)

        log.info(f"Successfully processed PDF for task {input_path}")

        # Clear GPU cache to free up memory
        # torch.cuda.empty_cache()

        return True  # Indicate success

    except subprocess.CalledProcessError as e:
        log.error(f"Error processing task {input_path}: {e.stderr}")
        return False  # Indicate failure

    # current_script_dir = os.path.dirname(os.path.abspath(__file__))
    # dest_dir = item[2]
    # filename = os.path.basename(item[1])
    # demo_name = remove_extension(filename)
    # pdf_path = item[1]
    # model_path = os.path.join(current_script_dir, f"magic-pdf.json")
    # pdf_bytes = open(pdf_path, "rb").read()
    # model_json = json.loads(open(model_path, "r", encoding="utf-8").read())
    # # model_json = []  # model_json传空list使用内置模型解析
    # jso_useful_key = {"_pdf_type": "", "model_list": model_json}
    # local_image_dir = os.path.join(dest_dir, 'images')
    # image_dir = str(os.path.basename(local_image_dir))
    # image_writer = DiskReaderWriter(local_image_dir)
    # pipe = UNIPipe(pdf_bytes, jso_useful_key, image_writer)
    # pipe.pipe_classify()
    # pipe.pipe_analyze()
    # pipe.pipe_parse()
    # md_content = pipe.pipe_mk_markdown(image_dir, drop_mode="none")
    # output_md_path = os.path.join(dest_dir, f"{demo_name}.md")
    # torch.cuda.empty_cache()
    #
    # with open(output_md_path, "w", encoding="utf-8") as f:
    #     f.write(md_content)
