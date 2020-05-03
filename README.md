# COCO_Preprocess

[LabelImg](https://github.com/tzutalin/labelImg)で画像に付けたBounding BoxのアノテーションをCOCOデータセットのフォーマットに変換するコードです。

## 使い方

```
python convert_to_coco.py \
    --annotation-fn <COCOフォーマットでのアノテーションファイルの保存先> \
    --image-root-dir <アノテーションされた画像を保存するディレクトリ名> \
    --annotation-dir <LabelImgによるアノテーションファイルがあるディレクトリ。空白区切りで複数可。>
    --copy-images
```

### Note

* アノテーションファイルはPascalVOCフォーマットで保存してください。
* 画像の位置は基本的にLabelImgによるアノテーションファイル中の情報を参考にしますが、アノテーションファイルと同じディレクトリに画像がある場合は `--same-dir` オプションを付ければそちらを探します。
  - 複数OSでアノテーションしたり、後から画像の位置を変えたりする場合に便利です。

* 対応している属性は以下に限ります。
  - images
    - file_name, height, width, id
  - annotations
    - image_id, bbox, category_id, id, iscrowd, area
  - categories
    - supercategory, name, id