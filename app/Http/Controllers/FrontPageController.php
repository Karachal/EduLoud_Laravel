<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Http\Controllers\Controller; // Make sure to import the base controller class if not already imported

class FrontPageController extends Controller
{
    public function index()
    {
        return view('frontpage');
    }
}
